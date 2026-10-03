package observe

import (
	"encoding/json"
	"fmt"
	"reflect"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/syndtr/goleveldb/leveldb/util"
)

type TicketEvent struct {
	Block        BlockReference
	Kind         string
	Transaction  common.Hash           `json:",omitempty"`
	TicketID     common.Hash           `json:",omitempty"`
	Ticket       *common.TicketDisplay `json:",omitempty"`
	RetreatIndex *int                  `json:",omitempty"`
	Return       string                `json:",omitempty"`
}

type TicketTimeline struct {
	Node             string
	Wallet           common.Address
	Sequence         uint64
	Anchor           BlockReference
	BaselineSequence uint64
	BaselineTimeUTC  time.Time
	From             uint64
	MaxBlocks        uint64
	Through          *BlockReference
	Blocks           BlockCoverage
	Status           string
	Issue            string `json:",omitempty"`
	Inventory        map[common.Hash]common.TicketDisplay
	Events           []TicketEvent
	Limitations      []string
}

func (history *History) TicketTimeline(node string, from, maxBlocks uint64) (TicketTimeline, error) {
	history.mu.Lock()
	defer history.mu.Unlock()
	wallet, exists := history.meta.Scope.Wallets[node]
	anchor := BlockReference{Number: history.meta.Scope.AnchorNumber, Hash: history.meta.Scope.AnchorHash}
	if from == 0 {
		from = anchor.Number + 1
	}
	if !exists || from <= anchor.Number || maxBlocks == 0 || maxBlocks > maxBackfillBlocks || from > ^uint64(0)-(maxBlocks-1) {
		return TicketTimeline{}, fmt.Errorf("ticket timeline requires a named wallet, a range after the anchor and 1 through 128 blocks")
	}
	state, err := history.load()
	if err != nil {
		return TicketTimeline{}, err
	}
	result := TicketTimeline{Node: node, Wallet: wallet, Sequence: state.Sequence, Anchor: anchor, From: from, MaxBlocks: maxBlocks, Status: "missing_baseline", Events: []TicketEvent{}, Limitations: []string{
		"derived from retained RPC evidence for one named wallet; not proof of endpoint honesty, state execution, consensus or finality",
		"baseline must be a matching anchor snapshot or explicit historical anchor inventory; other owners are outside this inventory",
		"return labels describe ticket interval-right rules, not liquid refunds or complete balance accounting",
		"events cover the requested range; earlier retained blocks are replayed for inventory; current branch freshness is in Blocks",
	}}
	result.Blocks = BlockCoverage{Node: node, StoredThrough: anchor, Status: "not_requested"}
	if coverage, ok := state.coverage[node]; ok {
		result.Blocks = coverage
	}
	parent, err := history.ticketBaseline(&result)
	if err != nil {
		return TicketTimeline{}, err
	}
	if parent == nil {
		return boundedTicketTimeline(result)
	}
	result.Through = &anchor
	result.Status = "complete_for_retained_prefix"
	path := state.blockPath(node)
	end := from + maxBlocks - 1
	iterator := history.db.NewIterator(util.BytesPrefix([]byte("event/")), nil)
	defer iterator.Release()
	for iterator.Next() {
		var event historyEvent
		if err := decodeHistory(iterator.Value(), &event); err != nil {
			return TicketTimeline{}, err
		}
		if event.Backfill == nil || event.Backfill.Node != node {
			continue
		}
		for _, evidence := range event.Backfill.Blocks {
			block, err := validateBlockEvidence(evidence)
			if err != nil {
				return TicketTimeline{}, err
			}
			height := block.NumberU64()
			if height <= result.Through.Number || height > end || height < anchor.Number || height-anchor.Number >= uint64(len(path)) || path[height-anchor.Number] != block.Hash() {
				continue
			}
			if height != result.Through.Number+1 || block.ParentHash() != result.Through.Hash {
				return TicketTimeline{}, fmt.Errorf("retained canonical ticket ancestry is out of order")
			}
			inventory, events, err := deriveTicketBlock(wallet, result.Inventory, parent, block, evidence.Receipts)
			if err != nil {
				result.Status, result.Issue = "incomplete", fmt.Sprintf("block %d: %v", height, err)
				return boundedTicketTimeline(result)
			}
			candidate := result
			candidate.Inventory = inventory
			candidate.Through = &BlockReference{Number: height, Hash: block.Hash()}
			if height >= from {
				candidate.Events = append(append([]TicketEvent{}, result.Events...), events...)
			}
			encoded, err := json.Marshal(candidate)
			if err != nil {
				return TicketTimeline{}, err
			}
			if len(encoded) > maxBackfillBytes {
				result.Status, result.Issue = "data_limit", "next block would exceed the 8 MiB report limit"
				return boundedTicketTimeline(result)
			}
			result, parent = candidate, block.Header()
		}
	}
	if err := iterator.Error(); err != nil {
		return TicketTimeline{}, err
	}
	expected := result.Blocks.StoredThrough.Number
	if end < expected {
		expected = end
	}
	if result.Through.Number != expected {
		return TicketTimeline{}, fmt.Errorf("retained canonical ticket ancestry is incomplete")
	}
	if from > result.Through.Number {
		result.Status = "range_not_retained"
	} else if result.Through.Number < result.Blocks.StoredThrough.Number {
		result.Status = "range_limit"
	}
	return boundedTicketTimeline(result)
}

func boundedTicketTimeline(result TicketTimeline) (TicketTimeline, error) {
	encoded, err := json.Marshal(result)
	if err != nil {
		return TicketTimeline{}, err
	}
	if len(encoded) > maxBackfillBytes {
		result.Status, result.Issue = "data_limit", "ticket report exceeds the 8 MiB limit"
		result.Through, result.Inventory, result.Events = nil, nil, []TicketEvent{}
	}
	return result, nil
}

func (history *History) ticketBaseline(result *TicketTimeline) (*types.Header, error) {
	var parent *types.Header
	iterator := history.db.NewIterator(util.BytesPrefix([]byte("event/")), nil)
	defer iterator.Release()
	for iterator.Next() {
		var event historyEvent
		if err := decodeHistory(iterator.Value(), &event); err != nil {
			return nil, err
		}
		var header *types.Header
		var tickets map[common.Hash]common.TicketDisplay
		if report := event.AnchorInventory; report != nil && report.Node == result.Node && report.Status == "ready" {
			header, tickets = report.Anchor.Header, report.Tickets
		}
		if event.Report != nil {
			for _, node := range event.Report.Nodes {
				if node.Name == result.Node && node.Identity == "matches" && node.Consistency == "stable" && node.TicketsKnown && node.Head != nil && node.Head.Hash == result.Anchor.Hash && node.Head.Header.Number.Uint64() == result.Anchor.Number {
					header, tickets = node.Head.Header, node.Tickets
				}
			}
		}
		if header == nil {
			continue
		}
		if !validTicketInventory(tickets, result.Wallet, result.Anchor.Number) {
			result.Status, result.Inventory = "invalid_baseline", nil
			return nil, nil
		}
		if parent != nil && !reflect.DeepEqual(result.Inventory, tickets) {
			result.Status, result.Inventory = "conflicting_baseline", nil
			return nil, nil
		}
		if parent == nil {
			parent, result.Inventory = header, tickets
			result.BaselineSequence, result.BaselineTimeUTC = event.Sequence, event.TimeUTC
		}
	}
	return parent, iterator.Error()
}
