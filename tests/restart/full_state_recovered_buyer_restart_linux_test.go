package restart

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateRecoveredBuyerRestart(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	owners := [2]common.Address{common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
	var source [2]peerPurchaseState
	readHandoverJSON(t, filepath.Join(root, "source-results", "stopped-purchases.json"), &source)
	var prior struct {
		Final *types.Header
		Stale *types.Transaction
	}
	readHandoverJSON(t, filepath.Join(root, "source-results", "stale-recovery-result.json"), &prior)
	if prior.Final.Hash() != common.HexToHash("0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061") || prior.Stale.Nonce() != 39 {
		t.Fatal("expected preserved stale-intent recovery result")
	}
	var saved types.Transaction
	requireNoError(t, saved.UnmarshalBinary(source[0].Saved))
	if source[0].Nonce != 43 || saved.Nonce() != 43 || saved.Hash() != common.HexToHash("0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a") || source[1].Nonce != 52 || len(source[1].Saved) != 0 {
		t.Fatal("source saved successor or canonical nonces differ")
	}
	var anchor *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			if f.chain.CurrentBlock().Hash() != prior.Final.Hash() {
				t.Fatal("copied canonical head differs")
			}
			anchor = f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			var records [2]*types.Transaction
			for j, owner := range owners {
				records[j] = readAutomaticPurchaseRecord(t, f.db, owner)
				if records[j] != nil && records[j].Hash() == prior.Stale.Hash() {
					t.Fatal("retired stale intent reappeared in copied database")
				}
			}
			if i == 0 && (records[0] == nil || records[0].Hash() != saved.Hash()) || i == 1 && records[1] != nil {
				t.Fatal("cold saved records differ from stopped services")
			}
			recordFundingInventory(t, root, "preflight-"+role, f, append([]common.Address{f.owner}, owners[:]...), records)
		}) {
			t.Fatal("restart preflight failed")
		}
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 5*time.Minute)}
	var initial [2]peerPurchaseState
	for i, node := range nodes {
		requirePausedPurchaseState(t, node, types.NewBlockWithHeader(prior.Final), source[i])
		initial[i] = readPeerPurchase(t, node)
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("fresh service must start with an empty transaction pool")
		}
	}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	startCompetingMiner(t, nodes[0])
	restored := awaitPeerPurchase(t, nodes[0], 43)
	if !bytes.Equal(restored.Saved, source[0].Saved) {
		t.Fatal("automatic recovery changed the saved successor's signed bytes")
	}
	requirePeerPurchaseStable(t, nodes[0], source[0].Saved, 43, types.NewBlockWithHeader(prior.Final))
	var paused [2]nodeRehearsalStatus
	for i, node := range nodes {
		paused[i] = node.status(t)
		requireRehearsalHead(t, paused[i], types.NewBlockWithHeader(prior.Final))
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "restored-purchase.json"), map[string]interface{}{
		"Initial": initial, "Restored": restored, "AfterRetryWindow": readPeerPurchase(t, nodes[0]),
		"Nodes": paused, "Transaction": &saved, "Raw": hexutil.Bytes(source[0].Saved), "StableSeconds": 6,
	}))
	startCompetingMiner(t, nodes[1])
	included := awaitLiveRepairReceipt(t, nodes, &saved, owners[0])
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "saved-inclusion.json"), map[string]interface{}{"Header": included.Header(), "Transaction": &saved}))
	trace, err := os.OpenFile(filepath.Join(root, "progress.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	observe := func() {
		row := equalWeightObservation{Phase: "restarted-automatic-buyers", ObservedUTC: time.Now().UTC()}
		for i, node := range nodes {
			row.Nodes[i], row.Purchases[i] = node.status(t), readPeerPurchase(t, node)
			if bytes.Equal(row.Purchases[i].Saved, source[0].Saved) && row.Purchases[i].Nonce > 44 {
				t.Fatal("included successor remained saved after later purchases")
			}
		}
		requireNoError(t, json.NewEncoder(trace).Encode(row))
	}
	live := awaitContinuousMinerProgressObserved(t, nodes[0], nodes[1], owners, [2]uint64{45, 54}, prior.Final.Number.Uint64(), 300*time.Second, observe)
	var purchases [2]types.Transactions
	var produced [2]uint64
	for number := prior.Final.Number.Uint64() + 1; number <= live.NumberU64(); number++ {
		block := readRecoveryNodeBlock(t, nodes[0], number)
		for i, owner := range owners {
			if block.Coinbase() == owner {
				produced[i]++
			}
		}
		for _, tx := range block.Transactions() {
			sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			matched := false
			for i, owner := range owners {
				if sender != owner {
					continue
				}
				if !tx.IsBuyTicketTx() || tx.Nonce() != source[i].Nonce+uint64(len(purchases[i])) || readCanonicalRepairReceipt(t, nodes, tx, owner) == nil {
					t.Fatal("restart continuation lacks sequential canonical native purchases")
				}
				purchases[i] = append(purchases[i], tx)
				matched = true
			}
			if !matched {
				t.Fatal("restart continuation contains an unexpected sender")
			}
		}
	}
	if len(purchases[0]) < 3 || len(purchases[1]) < 3 || produced[0] == 0 || produced[1] == 0 || purchases[0][0].Hash() != saved.Hash() {
		t.Fatal("both restarted owners must purchase and produce; donation must first execute the saved bytes")
	}
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		var receipt *types.Receipt
		requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", prior.Stale.Hash()))
		if receipt != nil || readCanonicalRepairReceipt(t, nodes, &saved, owners[0]) == nil {
			t.Fatal("retired stale intent or saved successor has an incorrect final canonical receipt")
		}
	}
	for _, node := range nodes {
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "restart-result.json"), map[string]interface{}{
		"Before": prior.Final, "Live": live.Header(), "Final": final.Header(), "SavedInclusion": included.Header(),
		"Purchases": purchases, "ProducedThroughLive": produced, "StaleHash": prior.Stale.Hash(),
		"NewFunding": false, "ManualSubmission": false, "RecordEdits": false, "StaleInjection": false,
	}))
	t.Logf("normal restart restored exact nonce-43 bytes from an empty pool, native inclusion at %d, purchases=%d/%d produced=%v; final=%d %s; no funding, manual submission or record edits", included.NumberU64(), len(purchases[0]), len(purchases[1]), produced, final.NumberU64(), final.Hash().Hex())
}

func TestFullStateRecoveredBuyerRestartColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	raw, err := os.ReadFile(filepath.Join(root, "source-results", "ordinary-transactions.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(raw, &ordinary))
	if len(ordinary) != 34 {
		t.Fatal("expected only the prior 34 allowlisted ordinary transactions")
	}
	auditRetainedPartitionCold(t, root, ordinary)
	var source struct{ Heads [2]*types.Header }
	readHandoverJSON(t, filepath.Join(root, "source-results", "cold-audit.json"), &source)
	var audit struct{ AdditionalFunding [2]map[common.Hash]uint64 }
	readHandoverJSON(t, filepath.Join(root, "cold-audit.json"), &audit)
	for i, entries := range audit.AdditionalFunding {
		if len(entries) != len(ordinary) {
			t.Fatal("cold history lost a previously included ordinary transaction")
		}
		for _, height := range entries {
			if height > source.Heads[i].Number.Uint64() {
				t.Fatal("restart continuation added an ordinary transfer")
			}
		}
	}
	t.Logf("cold restart ledgers retained exactly %d prior ordinary transactions; no new funding or nonce abandonment", len(ordinary))
}
