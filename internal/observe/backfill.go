package observe

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
)

const maxBackfillBlocks = 128
const maxBackfillBytes = 8 * 1024 * 1024

type BlockReference struct {
	Number uint64
	Hash   common.Hash
}

type BackfillReport struct {
	Node        string
	StartedUTC  time.Time
	FinishedUTC time.Time
	MaxBlocks   uint64
	ChainID     *hexutil.Big
	NetworkID   *string
	Genesis     *Block
	Anchor      *Block
	Head        *Block
	Base        *BlockReference
	Blocks      []BlockEvidence
	Status      string
}

type BlockCoverage struct {
	Node          string
	StoredThrough BlockReference
	ObservedHead  *BlockReference
	CheckedUTC    time.Time
	Status        string
}

func (history *History) Backfill(ctx context.Context, config Config, nodeName string, maxBlocks uint64, timeout time.Duration, now func() time.Time) (HistoryStatus, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	if err := history.CheckConfig(config); err != nil {
		return HistoryStatus{}, err
	}
	if maxBlocks == 0 || maxBlocks > maxBackfillBlocks || timeout <= 0 {
		return HistoryStatus{}, fmt.Errorf("backfill requires 1 through 128 blocks and a positive RPC timeout")
	}
	var selected *NodeConfig
	for i := range config.Nodes {
		if config.Nodes[i].Name == nodeName {
			selected = &config.Nodes[i]
		}
	}
	if selected == nil {
		return HistoryStatus{}, fmt.Errorf("backfill requires an explicitly configured node name")
	}
	state, err := history.load()
	if err != nil {
		return HistoryStatus{}, err
	}
	readContext, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	report := collectBackfill(readContext, config, *selected, state.blockPath(nodeName), maxBlocks, now)
	return history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, Backfill: &report})
}

func collectBackfill(ctx context.Context, config Config, node NodeConfig, path []common.Hash, maxBlocks uint64, now func() time.Time) (report BackfillReport) {
	report = BackfillReport{Node: node.Name, StartedUTC: now().UTC(), MaxBlocks: maxBlocks, Status: "unavailable"}
	defer func() { report.FinishedUTC = now().UTC() }()
	if node.Role == "retired" {
		report.Status = "retired"
		return
	}
	client, err := dial(ctx, node.Endpoint)
	if err != nil {
		return
	}
	defer client.Close()
	reader := readClient{client: client}
	if reader.call(ctx, &report.ChainID, "eth_chainId") != nil || reader.call(ctx, &report.NetworkID, "net_version") != nil {
		return
	}
	report.Genesis, err = reader.block(ctx, "0x0")
	if err != nil {
		return
	}
	report.Anchor, err = reader.block(ctx, hexutil.EncodeUint64(config.AnchorNumber))
	if err != nil {
		return
	}
	if !backfillIdentityMatches(scopeFor(config), &report) {
		if report.ChainID == nil || report.NetworkID == nil {
			return
		}
		report.Status = "identity_mismatch"
		return
	}
	report.Head, err = reader.block(ctx, "latest")
	if err != nil || report.Head.Header.Number.Uint64() < config.AnchorNumber {
		return
	}
	base, err := findBackfillBase(ctx, reader, config.AnchorNumber, path, report.Head.Header.Number.Uint64())
	if err != nil {
		return
	}
	report.Base = &base
	report.Status = "batch_limit"
	previous, bytesUsed := base, 0
	for previous.Number < report.Head.Header.Number.Uint64() && uint64(len(report.Blocks)) < maxBlocks {
		evidence, err := reader.blockEvidence(ctx, previous.Number+1)
		if err != nil {
			report.Status = "block_unavailable_or_invalid"
			break
		}
		block, err := validateBlockEvidence(evidence)
		if err != nil || block.ParentHash() != previous.Hash {
			report.Status = "block_unavailable_or_invalid"
			break
		}
		if len(report.Blocks) == 0 && base.Number-config.AnchorNumber+1 < uint64(len(path)) && block.Hash() == path[base.Number-config.AnchorNumber+1] {
			report.Status, report.Base, report.Blocks = "unstable", nil, nil
			return
		}
		encoded, err := json.Marshal(evidence)
		if err != nil || bytesUsed+len(encoded) > maxBackfillBytes {
			report.Status = "data_limit"
			break
		}
		bytesUsed += len(encoded)
		report.Blocks = append(report.Blocks, evidence)
		previous = BlockReference{Number: block.NumberU64(), Hash: block.Hash()}
	}
	if previous.Number == report.Head.Header.Number.Uint64() {
		if previous.Hash != report.Head.Hash {
			report.Status, report.Base, report.Blocks = "unstable", nil, nil
			return
		}
		report.Status = "complete_at_observation"
	}
	for _, reference := range []BlockReference{base, previous, {Number: report.Head.Header.Number.Uint64(), Hash: report.Head.Hash}} {
		again, err := reader.block(ctx, hexutil.EncodeUint64(reference.Number))
		if err != nil || again.Hash != reference.Hash {
			report.Status, report.Base, report.Blocks = "unstable", nil, nil
			return
		}
	}
	return
}

func findBackfillBase(ctx context.Context, reader readClient, anchor uint64, path []common.Hash, head uint64) (BlockReference, error) {
	low, high := anchor, anchor+uint64(len(path))-1
	if head < high {
		high = head
	}
	if low < high {
		block, err := reader.block(ctx, hexutil.EncodeUint64(high))
		if err != nil {
			return BlockReference{}, err
		}
		if block.Hash == path[high-anchor] {
			return BlockReference{Number: high, Hash: block.Hash}, nil
		}
		high--
	}
	for low < high {
		middle := low + (high-low)/2 + 1
		block, err := reader.block(ctx, hexutil.EncodeUint64(middle))
		if err != nil {
			return BlockReference{}, err
		}
		if block.Hash == path[middle-anchor] {
			low = middle
		} else {
			high = middle - 1
		}
	}
	return BlockReference{Number: low, Hash: path[low-anchor]}, nil
}

func backfillIdentityMatches(scope HistoryScope, report *BackfillReport) bool {
	return report.ChainID != nil && report.NetworkID != nil && report.ChainID.ToInt().String() == scope.ChainID && *report.NetworkID == scope.NetworkID &&
		validBackfillHeader(report.Genesis) && report.Genesis.Header.Number.Sign() == 0 && report.Genesis.Hash == scope.Genesis &&
		validBackfillHeader(report.Anchor) && report.Anchor.Header.Number.Uint64() == scope.AnchorNumber && report.Anchor.Hash == scope.AnchorHash
}

func validBackfillHeader(block *Block) bool {
	return block != nil && block.Header != nil && block.Header.Number != nil && block.Header.Number.IsUint64() && block.Hash == block.Header.Hash()
}
