package observe

import (
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"sort"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func Collect(ctx context.Context, config Config, timeout time.Duration, now func() time.Time) (Report, error) {
	report := Report{Version: 1, StartedUTC: now().UTC(), Comparison: Comparison{Status: "not_requested"}, Limitations: []string{
		"one bounded observation; no liveness threshold, historical backfill, incident closure or notifications",
		"saved controller intent is unknown; supplied signed transactions are tracking inputs, not live record proof",
		"funding and payload checks are diagnostics, not complete pool admission or producer eligibility checks",
		"RPC observations do not attest executable identity, consensus validity or future finality",
	}}
	if err := ValidateConfig(config); err != nil {
		return report, err
	}
	if timeout <= 0 {
		return report, fmt.Errorf("positive collection timeout required")
	}
	readers := make([]readClient, len(config.Nodes))
	for i, node := range config.Nodes {
		observation := Observation{Name: node.Name, Role: node.Role, Wallet: node.Wallet, StartedUTC: now().UTC(), Identity: "unknown", Consistency: "unknown", SavedIntent: "unknown"}
		if node.Role == "retired" {
			observation.Consistency = "not_applicable"
			observation.FinishedUTC = now().UTC()
			report.Nodes = append(report.Nodes, observation)
			continue
		}
		sampleContext, cancel := context.WithTimeout(ctx, timeout)
		client, err := dial(sampleContext, node.Endpoint)
		if err != nil {
			observation.issue("endpoint", "unavailable")
		} else {
			defer client.Close()
			readers[i] = readClient{client: client}
			collectNode(sampleContext, readers[i], config, &observation, now)
		}
		cancel()
		observation.FinishedUTC = now().UTC()
		report.Nodes = append(report.Nodes, observation)
	}
	if len(readers) == 2 {
		comparisonContext, cancel := context.WithTimeout(ctx, timeout)
		report.Comparison = compareNodes(comparisonContext, readers, report.Nodes)
		cancel()
	}
	report.FinishedUTC = now().UTC()
	return report, nil
}

func collectNode(ctx context.Context, reader readClient, config Config, out *Observation, now func() time.Time) {
	out.read(ctx, reader, &out.ClientVersion, "web3_clientVersion")
	out.read(ctx, reader, &out.ChainID, "eth_chainId")
	out.read(ctx, reader, &out.NetworkID, "net_version")
	out.Head = out.readBlock(ctx, reader, "latest")
	out.Genesis = out.readBlock(ctx, reader, "0x0")
	out.Anchor = out.readBlock(ctx, reader, hexutil.EncodeUint64(config.AnchorNumber))
	if out.ChainID != nil && out.NetworkID != nil && out.Genesis != nil && out.Anchor != nil {
		out.Identity = "matches"
		if (*big.Int)(out.ChainID).String() != config.ChainID || *out.NetworkID != config.NetworkID || out.Genesis.Hash != config.Genesis || out.Anchor.Hash != config.AnchorHash {
			out.Identity = "mismatch"
			out.issue("identity", "mismatch")
		}
	} else {
		out.issue("identity", "incomplete")
	}
	out.read(ctx, reader, &out.Syncing, "eth_syncing")
	if string(out.Syncing) != "false" {
		var progress struct {
			CurrentBlock *hexutil.Uint64
			HighestBlock *hexutil.Uint64
		}
		if json.Unmarshal(out.Syncing, &progress) != nil || progress.CurrentBlock == nil || progress.HighestBlock == nil {
			out.Syncing = nil
			out.issue("eth_syncing", "invalid_or_missing")
		}
	}
	out.read(ctx, reader, &out.Mining, "eth_mining")
	out.read(ctx, reader, &out.AutoBuy, "fsn_isAutoBuyTicket")
	out.read(ctx, reader, &out.Coinbase, "eth_coinbase")
	out.read(ctx, reader, &out.Peers, "net_peerCount")
	if out.Mining == nil || out.AutoBuy == nil || out.Coinbase == nil || out.Peers == nil || out.ClientVersion == nil {
		out.issue("node_status", "incomplete")
	}
	if out.Role == "producer" && out.Coinbase != nil && *out.Coinbase != out.Wallet {
		out.issue("coinbase", "unexpected_wallet")
	}
	if out.Role == "producer" && string(out.Syncing) == "false" && (out.Mining != nil && !*out.Mining || out.AutoBuy != nil && !*out.AutoBuy) {
		out.issue("producer_flags", "disabled_observed")
	}
	if out.Head == nil {
		return
	}
	if out.Head.TotalDifficulty == nil {
		out.issue("total_difficulty", "unknown")
	}
	if out.Head.Header.Number.Uint64() < config.AnchorNumber {
		out.issue("head", "below_anchor")
	}
	number := hexutil.EncodeUint64(out.Head.Header.Number.Uint64())
	out.read(ctx, reader, &out.Nonce, "eth_getTransactionCount", out.Wallet, number)
	out.read(ctx, reader, &out.LiquidWei, "fsn_getBalance", common.SystemAssetID, out.Wallet, number)
	out.read(ctx, reader, &out.TimeLocks, "fsn_getRawTimeLockBalance", common.SystemAssetID, out.Wallet, number)
	if out.LiquidWei != nil {
		value, ok := new(big.Int).SetString(*out.LiquidWei, 10)
		if !ok || value.Sign() < 0 {
			out.LiquidWei = nil
			out.issue("balance", "invalid")
		}
	}
	if out.TimeLocks != nil && !validTimeLocks(out.TimeLocks) {
		out.TimeLocks = nil
		out.issue("time_locks", "invalid")
	}
	if out.Nonce == nil || out.LiquidWei == nil || out.TimeLocks == nil {
		out.issue("account", "incomplete")
	}
	out.TicketsKnown = out.read(ctx, reader, &out.Tickets, "fsn_allTicketsByAddress", out.Wallet, number)
	for id, ticket := range out.Tickets {
		if id == (common.Hash{}) || ticket.Owner != out.Wallet || ticket.Value == nil || ticket.Value.Sign() < 0 || ticket.StartTime >= ticket.ExpireTime {
			out.TicketsKnown = false
			out.issue("tickets", "invalid")
		}
	}
	collectPool(ctx, reader, out)
	for _, raw := range config.Tracked {
		var tx types.Transaction
		_ = tx.UnmarshalBinary(raw)
		owner, _ := types.Sender(types.LatestSignerForChainID(tx.ChainId()), &tx)
		if owner == out.Wallet {
			out.Tracked = append(out.Tracked, observeTransaction(ctx, reader, out, &tx, raw, now()))
		}
	}
	again := out.readBlock(ctx, reader, number)
	if again != nil && again.Hash == out.Head.Hash {
		out.Consistency = "stable"
	} else {
		out.Consistency = "changed_or_unavailable"
		out.issue("snapshot", "invalidated")
	}
	if out.Consistency != "stable" || out.Identity != "matches" {
		for i := range out.Tracked {
			out.Tracked[i].Inclusion, out.Tracked[i].Funding, out.Tracked[i].Payload, out.Tracked[i].NonceRelation = "unknown", "unknown", "unknown", "unknown"
		}
	}
}

func validTimeLocks(locks *common.TimeLock) bool {
	for _, item := range locks.Items {
		if item == nil || item.Value == nil {
			return false
		}
	}
	return locks.IsValid() == nil
}

func collectPool(ctx context.Context, reader readClient, out *Observation) {
	var pool *struct {
		Pending map[common.Address]map[string]*types.Transaction
		Queued  map[common.Address]map[string]*types.Transaction
	}
	if !out.read(ctx, reader, &pool, "txpool_content") || pool == nil || pool.Pending == nil || pool.Queued == nil {
		out.issue("pool", "incomplete")
		return
	}
	out.PoolKnown = true
	for i, queue := range []map[common.Address]map[string]*types.Transaction{pool.Pending, pool.Queued} {
		for key, tx := range queue[out.Wallet] {
			if tx == nil || len(out.Pool) >= 256 {
				out.PoolKnown = false
				continue
			}
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			if err != nil || owner != out.Wallet || new(big.Int).SetUint64(tx.Nonce()).String() != key || out.ChainID == nil || tx.ChainId().Cmp((*big.Int)(out.ChainID)) != 0 {
				out.PoolKnown = false
				continue
			}
			out.Pool = append(out.Pool, PoolTransaction{Queue: []string{"pending", "queued"}[i], Transaction: tx})
		}
	}
	if !out.PoolKnown {
		out.issue("pool", "invalid_or_truncated")
	}
	sort.Slice(out.Pool, func(i, j int) bool {
		return out.Pool[i].Transaction.Hash().Hex() < out.Pool[j].Transaction.Hash().Hex()
	})
}

func (out *Observation) read(ctx context.Context, reader readClient, result interface{}, method string, args ...interface{}) bool {
	if reader.call(ctx, result, method, args...) != nil {
		_ = json.Unmarshal([]byte("null"), result)
		out.issue(method, "rpc_failed")
		return false
	}
	return true
}

func (out *Observation) readBlock(ctx context.Context, reader readClient, number string) *Block {
	block, err := reader.block(ctx, number)
	if err != nil {
		out.issue("block:"+number, "unavailable_or_invalid")
		return nil
	}
	return block
}

func (out *Observation) issue(field, code string) {
	out.Issues = append(out.Issues, Issue{Field: field, Code: code})
}

func compareNodes(ctx context.Context, readers []readClient, observations []Observation) Comparison {
	result := Comparison{Status: "unavailable"}
	for i, observation := range observations {
		if readers[i].client == nil || observation.Head == nil || observation.Consistency != "stable" || observation.Identity != "matches" {
			return result
		}
	}
	height := observations[0].Head.Header.Number.Uint64()
	if other := observations[1].Head.Header.Number.Uint64(); other < height {
		height = other
	}
	result.Height = height
	for _, reader := range readers {
		block, err := reader.block(ctx, hexutil.EncodeUint64(height))
		if err != nil {
			return result
		}
		result.Hashes = append(result.Hashes, block.Hash)
	}
	for i, reader := range readers {
		block, err := reader.block(ctx, hexutil.EncodeUint64(height))
		if err != nil || block.Hash != result.Hashes[i] {
			result.Status = "unstable"
			return result
		}
	}
	result.Status = "same_at_common_height"
	if result.Hashes[0] != result.Hashes[1] {
		result.Status = "divergent_at_common_height"
	}
	return result
}
