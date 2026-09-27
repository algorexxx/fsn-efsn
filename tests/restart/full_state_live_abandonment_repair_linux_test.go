package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateLiveAbandonmentRepair(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	owners := [2]common.Address{common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
	var prior struct {
		Final *types.Header
		Cold  peerPurchaseState
	}
	readHandoverJSON(t, filepath.Join(root, "source-results", "reorg-result.json"), &prior)
	var saved types.Transaction
	requireNoError(t, saved.UnmarshalBinary(prior.Cold.Saved))
	if prior.Final.Hash() != common.HexToHash("0xd20a058d9830fb8b93df0e4ecb0874132c40254020ae3ea3d0ed646434ab3347") || prior.Cold.Nonce != 39 || saved.Nonce() != 43 || saved.Hash() != common.HexToHash("0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a") {
		t.Fatal("expected the preserved abandonment rollback and unchanged saved successor")
	}
	var local struct{ Final *types.Header }
	readHandoverJSON(t, filepath.Join(root, "source-results", "stale-recovery-result.json"), &local)
	if local.Final.Hash() != common.HexToHash("0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061") {
		t.Fatal("expected the original branch before rollback")
	}
	heads := [2]*types.Header{local.Final, prior.Final}
	var anchor *types.Block
	var expected [2]peerPurchaseState
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			if f.chain.CurrentBlock().Hash() != heads[i].Hash() {
				t.Fatal("copied rollback head differs")
			}
			anchor = f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			var original []struct {
				Nonce uint64
				Saved hexutil.Bytes
			}
			readHandoverJSON(t, filepath.Join(root, "source-results", "cold-intents-"+role+".json"), &original)
			if len(original) != 2 {
				t.Fatal("expected two preserved wallet records")
			}
			state, err := f.chain.State()
			requireNoError(t, err)
			var records [2]*types.Transaction
			for j, owner := range owners {
				records[j] = readAutomaticPurchaseRecord(t, f.db, owner)
				var raw []byte
				if records[j] != nil {
					raw, err = records[j].MarshalBinary()
					requireNoError(t, err)
				}
				if !bytes.Equal(raw, original[j].Saved) || state.GetNonce(owner) != original[j].Nonce || original[j].Nonce != [2][2]uint64{{43, 52}, {39, 63}}[i][j] {
					t.Fatal("cold wallet record or nonce differs from source")
				}
			}
			expected[i] = peerPurchaseState{Nonce: original[i].Nonce, Saved: original[i].Saved}
			recordFundingInventory(t, root, "preflight-"+role, f, append([]common.Address{f.owner}, owners[:]...), records)
		}) {
			t.Fatal("rollback-repair preflight failed")
		}
	}
	var branch types.Blocks
	originals := make(map[uint64]*types.Transaction)
	for number := 53; number <= 60; number++ {
		raw, err := os.ReadFile(filepath.Join(root, "source-results", "old-branch", fmt.Sprintf("block-%02d.rlp", number)))
		requireNoError(t, err)
		var block *types.Block
		requireNoError(t, rlp.DecodeBytes(raw, &block))
		branch = append(branch, block)
		for _, tx := range block.Transactions() {
			sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			if sender == owners[0] {
				originals[tx.Nonce()] = tx
			}
		}
	}
	if len(originals) != 4 || originals[39] == nil || originals[39].Hash() != common.HexToHash("0xdfe37cb273c558caad05568f61fc1096f8b1752af99dddf80e9c8adcad19fd83") {
		t.Fatal("expected original abandonment and three displaced purchases")
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 12*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 12*time.Minute)}
	for i, node := range nodes {
		requirePausedPurchaseState(t, node, types.NewBlockWithHeader(heads[i]), expected[i])
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("recovery requires initially empty pools")
		}
	}
	startCompetingMiner(t, nodes[0])
	restored := awaitPeerPurchase(t, nodes[0], 43)
	if !bytes.Equal(restored.Saved, prior.Cold.Saved) {
		t.Fatal("automatic restoration changed the saved successor")
	}
	requirePeerPurchaseStable(t, nodes[0], prior.Cold.Saved, 43, types.NewBlockWithHeader(local.Final))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "restored-purchase.json"), restored))
	trace, err := os.OpenFile(filepath.Join(root, "progress.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	poolObserver := observeDeliveryPools(t, root, nodes)
	observe := func() {
		poolObserver()
		row := equalWeightObservation{Phase: "ordinary-live-rollback", ObservedUTC: time.Now().UTC()}
		for i, node := range nodes {
			row.Nodes[i], row.Purchases[i] = node.status(t), readPeerPurchase(t, node)
		}
		requireNoError(t, json.NewEncoder(trace).Encode(row))
	}
	startCompetingMiner(t, nodes[1])
	observe()
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	captured := [2]map[uint64]*types.Transaction{make(map[uint64]*types.Transaction), make(map[uint64]*types.Transaction)}
	gap := awaitLivePurchaseGapObserved(t, nodes, owners, captured, prior.Final.Number.Uint64(), observe)
	if gap.index != 0 || gap.nonce != 41 || gap.saved.Hash() != saved.Hash() {
		t.Fatalf("expected unchanged saved 43 after automatic reinclusion of 39 and 40; gap owner=%d nonce=%d", gap.index, gap.nonce)
	}
	for _, node := range nodes {
		if readRecoveryNodeBlock(t, node, prior.Final.Number.Uint64()).Hash() != prior.Final.Hash() {
			t.Fatal("ordinary synchronization did not accept the heavier compatible branch")
		}
	}
	cancel := originals[39]
	if cancel.To() == nil || *cancel.To() != owners[0] || cancel.Value().Sign() != 0 || cancel.Gas() != 21000 || len(cancel.Data()) != 0 {
		t.Fatal("preserved abandonment is not the reviewed zero-value self-transfer")
	}
	receipt := awaitLiveFundingTransfer(t, nodes, cancel)
	if len(receipt.Logs) != 0 || receipt.BlockNumber.Uint64() <= prior.Final.Number.Uint64() {
		t.Fatal("automatically reincluded abandonment must have a new canonical receipt without ticket creation")
	}
	included := awaitLiveRepairReceipt(t, nodes, originals[40], owners[0])
	if included.NumberU64() <= prior.Final.Number.Uint64() {
		t.Fatal("lowest purchase must be automatically reincluded above the heavier branch")
	}
	raw, err := cancel.MarshalBinary()
	requireNoError(t, err)
	after := readPeerPurchase(t, nodes[0])
	if after.Nonce != 41 || !bytes.Equal(after.Saved, prior.Cold.Saved) || len(after.Pending)+len(after.Queued) != 0 {
		t.Fatal("receipt-aware diagnosis changed before manual recovery")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "automatic-reinclusion.json"), map[string]interface{}{
		"Transaction": cancel, "Raw": hexutil.Bytes(raw), "Receipt": receipt, "After": after,
		"Purchase": originals[40], "PurchaseBlock": included.Header(), "GapHead": gap.head.Header(),
		"ManualSubmissions": 0,
	}))
	repair := repairFullStateGap(t, root, nodes, owners, gap, originals, branch, false, true)
	var live *types.Block
	var purchases [2]types.Transactions
	var produced [2]uint64
	if repair.FundingFailure == "" {
		live = awaitContinuousMinerProgressObserved(t, nodes[0], nodes[1], owners, [2]uint64{45, 65}, prior.Final.Number.Uint64(), 300*time.Second, observe)
		for number := prior.Final.Number.Uint64() + 1; number <= live.NumberU64(); number++ {
			block := readRecoveryNodeBlock(t, nodes[0], number)
			for i, owner := range owners {
				if block.Coinbase() == owner {
					produced[i]++
				}
			}
			for _, tx := range block.Transactions() {
				if tx.Hash() == cancel.Hash() {
					continue
				}
				sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
				requireNoError(t, err)
				matched := false
				for i, owner := range owners {
					if sender != owner {
						continue
					}
					if !tx.IsBuyTicketTx() || tx.Nonce() != [2]uint64{40, 63}[i]+uint64(len(purchases[i])) || readCanonicalRepairReceipt(t, nodes, tx, owner) == nil {
						t.Fatal("repair continuation lacks sequential native purchases")
					}
					purchases[i] = append(purchases[i], tx)
					matched = true
				}
				if !matched {
					t.Fatal("unexpected transaction in repair continuation")
				}
			}
		}
		if repair.OriginalsIncluded != 2 || repair.Successors < 2 || len(purchases[0]) < 6 || len(purchases[1]) < 3 || produced[0] == 0 || produced[1] == 0 || purchases[0][3].Hash() != saved.Hash() {
			t.Fatal("repair must execute originals, saved intent, fresh successors and both owners' blocks")
		}
		for i := 0; i < 3; i++ {
			if purchases[0][i].Hash() != originals[uint64(40+i)].Hash() {
				t.Fatal("manual recovery replaced an original purchase")
			}
		}
	}
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	observe()
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		node.stop(t, false)
	}
	repair.Final = final.Hash()
	var liveHeader *types.Header
	if live != nil {
		liveHeader = live.Header()
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "repair-result.json"), map[string]interface{}{"Before": prior.Final, "LocalBefore": local.Final, "ServicesRestarted": false, "ExplicitDownloader": false, "AutomaticReinclusion": []uint64{39, 40}, "ManualNonces": []uint64{41, 42}, "Live": liveHeader, "Final": final.Header(), "Repair": repair, "Abandonment": cancel, "AbandonmentReceipt": receipt, "Purchases": purchases, "ProducedThroughLive": produced, "NewFunding": false, "RecordEdits": false, "ResignedOriginals": false, "HeldSigner": false}))
	if repair.FundingFailure != "" {
		t.Fatalf("preserved rollback repair remains unfunded: %s", repair.FundingFailure)
	}
	t.Logf("ordinary rollback automatically reincluded abandonment 39 and purchase 40; exact originals 41-42 repaired; saved 43 and fresh successors executed; both producers resumed; purchases=%d/%d produced=%v final=%d %s", len(purchases[0]), len(purchases[1]), produced, final.NumberU64(), final.Hash().Hex())
}

func TestFullStateLiveAbandonmentRepairColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	raw, err := os.ReadFile(filepath.Join(root, "source-results", "ordinary-transactions.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(raw, &ordinary))
	if len(ordinary) != 34 {
		t.Fatal("expected existing funding and original abandonment allowlist")
	}
	auditRetainedPartitionCold(t, root, ordinary)
}
