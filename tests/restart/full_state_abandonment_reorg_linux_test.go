package restart

import (
	"bytes"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateAbandonmentReorg(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	owners := [2]common.Address{common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
	var source [2]peerPurchaseState
	readHandoverJSON(t, filepath.Join(root, "source-results", "stopped-purchases.json"), &source)
	var saved types.Transaction
	requireNoError(t, saved.UnmarshalBinary(source[0].Saved))
	if source[0].Nonce != 43 || saved.Hash() != common.HexToHash("0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a") {
		t.Fatal("expected the preserved saved nonce-43 successor")
	}
	raw, err := os.ReadFile(filepath.Join(root, "source-results", "ordinary-transactions.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(raw, &ordinary))
	if len(ordinary) != 34 || ordinary[33].Hash() != common.HexToHash("0xdfe37cb273c558caad05568f61fc1096f8b1752af99dddf80e9c8adcad19fd83") {
		t.Fatal("expected prior funding and explicit nonce-39 abandonment")
	}
	var anchor, old, fork, remote *types.Block
	var oldTD *big.Int
	var displaced types.Blocks
	if !t.Run("retain-old-branch", func(t *testing.T) {
		f, _, funding := openFullStateHandover(t, filepath.Join(root, "producer"))
		old = f.chain.CurrentBlock()
		if old.Hash() != common.HexToHash("0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061") || readAutomaticPurchaseRecord(t, f.db, owners[0]).Hash() != saved.Hash() {
			t.Fatal("copied recovered head or saved record differs")
		}
		anchor = f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
		fork = f.chain.GetBlockByNumber(15130132)
		oldTD = f.chain.GetTd(old.Hash(), old.NumberU64())
		for number := fork.NumberU64() + 1; number <= old.NumberU64(); number++ {
			displaced = append(displaced, f.chain.GetBlockByNumber(number))
		}
		recordAbandonmentBranch(t, root, "old-branch", f, ordinary)
		recordFundingInventory(t, root, "preflight-producer", f, append([]common.Address{f.owner}, owners[:]...), [2]*types.Transaction{&saved, nil})
	}) {
		t.Fatal("old branch preflight failed")
	}
	if !t.Run("build-competing-branch", func(t *testing.T) {
		f, _, _ := openFullStateHandover(t, filepath.Join(root, "verifier"))
		if f.chain.CurrentBlock().Hash() != common.HexToHash("0x1c856076d9f7d8ab6f426a50684e581f48688e5dc41bb4bc81cee0f4d0d977cc") || f.chain.GetBlockByHash(old.Hash()) != nil {
			t.Fatal("competing source must precede funding and not know the recovered tip")
		}
		for number := 51; number <= 52; number++ {
			encoded, err := os.ReadFile(filepath.Join(root, "old-branch", fmt.Sprintf("block-%02d.rlp", number)))
			requireNoError(t, err)
			var block *types.Block
			requireNoError(t, rlp.DecodeBytes(encoded, &block))
			f.importBlock(t, block)
		}
		if f.chain.CurrentBlock().Hash() != fork.Hash() {
			t.Fatal("competing branch did not retain exact pre-abandonment funding")
		}
		keyBytes := make([]byte, 32)
		keyBytes[31] = 3
		key, err := crypto.ToECDSA(keyBytes)
		requireNoError(t, err)
		f.key, f.owner = key, crypto.PubkeyToAddress(key.PublicKey)
		for f.chain.GetTd(f.chain.CurrentBlock().Hash(), f.chain.CurrentBlock().NumberU64()).Cmp(new(big.Int).Add(oldTD, big.NewInt(6))) <= 0 {
			parent := f.chain.CurrentBlock()
			if parent.NumberU64() > old.NumberU64()+32 || parent.Time()+121 >= uint64(time.Now().Unix()) {
				t.Fatal("competing branch exceeds height or wall-time budget")
			}
			purchase := f.signPurchase(t, parent.Time(), parent.Time()+30*24*3600)
			block := f.buildBlockWithTransactions(t, parent.Time()+121, []*types.Transaction{purchase})
			f.importBlock(t, block)
		}
		remote = f.chain.CurrentBlock()
		state, err := f.chain.State()
		requireNoError(t, err)
		if state.GetNonce(owners[0]) != 39 || f.chain.GetBlockByHash(old.Hash()) != nil {
			t.Fatal("competing branch consumed donation nonce or contains old recovered tip")
		}
		recordAbandonmentBranch(t, root, "competing-branch", f, ordinary[:33])
		recordFundingInventory(t, root, "preflight-verifier", f, append([]common.Address{common.HexToAddress("0x7e5f4552091a69125d5dfcb7b8c2659029395bdf")}, owners[:]...), [2]*types.Transaction{readAutomaticPurchaseRecord(t, f.db, owners[0]), readAutomaticPurchaseRecord(t, f.db, owners[1])})
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "branch-plan.json"), map[string]interface{}{"Old": old.Header(), "OldTD": oldTD.String(), "Fork": fork.Header(), "Remote": remote.Header(), "RemoteTD": f.chain.GetTd(remote.Hash(), remote.NumberU64()).String(), "NewFunding": false, "HeadRewind": false, "RecordEdits": false}))
	}) {
		t.Fatal("competing branch preparation failed")
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 5*time.Minute)}
	requirePausedPurchaseState(t, nodes[0], old, source[0])
	for _, node := range nodes {
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("fresh services require empty pools")
		}
	}
	startHeldPurchaseWorker(t, nodes[0])
	before := awaitPeerPurchase(t, nodes[0], 43)
	requirePeerPurchaseStable(t, nodes[0], source[0].Saved, 43, old)
	syncRecoveryNode(t, nodes[0], nodes[1], remote)
	awaitRehearsal(t, 10*time.Second, func() bool {
		state := readPeerPurchase(t, nodes[0])
		return state.Nonce == 39 && len(state.Pending) == 2 && state.Pending[0].Hash() == ordinary[33].Hash() && state.Pending[1].Nonce() == 40 && len(state.Queued) == 0
	})
	live := recordAbandonmentReorgWindow(t, root, "live-rollback", nodes[0], remote, source[0].Saved, displaced, false)
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
		node.stop(t, false)
	}
	requirePurchaseLogContains(t, paths[0], "another ticket purchase")
	nodes[0] = startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute)
	if state := readPeerPurchase(t, nodes[0]); state.Nonce != 39 || len(state.Pending)+len(state.Queued) != 0 || !bytes.Equal(state.Saved, source[0].Saved) {
		t.Fatal("cold restart changed nonce or saved intent, or restored a disabled journal")
	}
	startHeldPurchaseWorker(t, nodes[0])
	cold := recordAbandonmentReorgWindow(t, root, "cold-rollback", nodes[0], remote, source[0].Saved, displaced, true)
	stopPeerAutoMiner(t, nodes[0])
	nodes[0].stop(t, false)
	requirePurchaseLogContains(t, paths[0], "needs nonce 43, current nonce is 39")
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "reorg-result.json"), map[string]interface{}{
		"Before": before, "Live": live, "Cold": cold, "Old": old.Header(), "Final": remote.Header(), "Fork": fork.Header(),
		"DownloaderRequested": true, "HeldDonationSigner": true, "MiningContinuation": false,
		"NewFunding": false, "ManualSubmission": false, "RecordEdits": false,
	}))
	t.Logf("compatible rollback removed nonce-39 abandonment and purchases 40-42; canonical nonce 43 -> 39, exact saved 43 retained; live pool contains abandonment + purchase 40; empty-pool cold restart reports gap without re-signing; head=%d %s", remote.NumberU64(), remote.Hash().Hex())
}

func recordAbandonmentBranch(t *testing.T, root, label string, f *fixture, ordinary types.Transactions) {
	t.Helper()
	artifacts := filepath.Join(root, label)
	requireNoError(t, os.Mkdir(artifacts, 0700))
	allowed := make(map[common.Hash]uint64)
	for number := uint64(15130081); number <= f.chain.CurrentBlock().NumberU64(); number++ {
		block := f.chain.GetBlockByNumber(number)
		recordFullStateHandoverBlock(t, f, artifacts, 15130080, block)
		for _, tx := range block.Transactions() {
			for _, candidate := range ordinary {
				if tx.Hash() == candidate.Hash() {
					allowed[tx.Hash()] = number
				}
			}
		}
	}
	if len(allowed) != len(ordinary) {
		t.Fatal("branch lost an expected ordinary transaction")
	}
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	auditFullStateParticipantTransfers(t, artifacts, int(f.chain.CurrentBlock().NumberU64()-15130080), allowed)
}

func recordAbandonmentReorgWindow(t *testing.T, root, label string, node *rehearsalNode, head *types.Block, saved []byte, displaced types.Blocks, empty bool) peerPurchaseState {
	t.Helper()
	var rows []map[string]interface{}
	var last peerPurchaseState
	for start := time.Now(); time.Since(start) < 12*time.Second; time.Sleep(time.Second) {
		last = readPeerPurchase(t, node)
		status := node.status(t)
		requireRehearsalHead(t, status, head)
		if last.Nonce != 39 || !bytes.Equal(last.Saved, saved) || !status.Mining || !status.AutoBuy || status.Signatures != 0 || len(last.Queued) != 0 || (empty && len(last.Pending) != 0) || (!empty && len(last.Pending) != 2) {
			t.Fatal("rolled-back buyer changed saved bytes, nonce or expected pool, or signed a block")
		}
		var recovered []map[string]interface{}
		for _, block := range displaced {
			for index, tx := range block.Transactions() {
				sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
				requireNoError(t, err)
				if sender != common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf") {
					continue
				}
				var receipt *types.Receipt
				requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
				if receipt != nil || readRecoveryNodeBlock(t, node, block.NumberU64()).Hash() == block.Hash() {
					t.Fatal("displaced transaction retained canonical inclusion")
				}
				var raw hexutil.Bytes
				requireNoError(t, node.call(t, &raw, "eth_getRawTransactionByBlockHashAndIndex", block.Hash(), hexutil.Uint64(index)))
				expected, err := tx.MarshalBinary()
				requireNoError(t, err)
				if !bytes.Equal(raw, expected) {
					t.Fatal("old-block RPC did not retain exact signed bytes")
				}
				recovered = append(recovered, map[string]interface{}{"Nonce": tx.Nonce(), "Hash": tx.Hash(), "Raw": raw, "Block": block.Hash(), "Height": block.NumberU64(), "Index": index, "Receipt": receipt})
			}
		}
		if len(recovered) != 4 {
			t.Fatal("expected displaced abandonment and three confirmed purchases")
		}
		rows = append(rows, map[string]interface{}{"ObservedUTC": time.Now().UTC(), "Node": status, "Purchase": last, "Recovered": recovered})
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, label+".json"), rows))
	return last
}

func TestFullStateAbandonmentReorgColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	raw, err := os.ReadFile(filepath.Join(root, "source-results", "ordinary-transactions.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(raw, &ordinary))
	if len(ordinary) != 34 {
		t.Fatal("expected preserved ordinary transaction allowlist")
	}
	auditRetainedPartitionCold(t, root, ordinary)
	var result struct{ Final *types.Header }
	readHandoverJSON(t, filepath.Join(root, "reorg-result.json"), &result)
	var audit struct {
		Heads             [2]*types.Header
		AdditionalFunding [2]map[common.Hash]uint64
	}
	readHandoverJSON(t, filepath.Join(root, "cold-audit.json"), &audit)
	for i, entries := range audit.AdditionalFunding {
		if audit.Heads[i].Hash() != result.Final.Hash() || len(entries) != 33 || entries[ordinary[33].Hash()] != 0 {
			t.Fatal("cold chain did not retain funding and remove abandonment")
		}
	}
}
