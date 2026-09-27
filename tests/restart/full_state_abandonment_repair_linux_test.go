package restart

import (
	"bytes"
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

func TestFullStateAbandonmentRepair(t *testing.T) {
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
	var anchor *types.Block
	var expected [2]peerPurchaseState
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			if f.chain.CurrentBlock().Hash() != prior.Final.Hash() {
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
				if !bytes.Equal(raw, original[j].Saved) || state.GetNonce(owner) != original[j].Nonce || original[j].Nonce != [2]uint64{39, 63}[j] {
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
		requirePausedPurchaseState(t, node, types.NewBlockWithHeader(prior.Final), expected[i])
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("recovery requires initially empty pools")
		}
	}
	for _, block := range branch {
		for _, tx := range block.Transactions() {
			if original := originals[tx.Nonce()]; original != nil && original.Hash() == tx.Hash() {
				requireDisplacedPurchaseRPC(t, nodes[0], block, tx)
			}
		}
	}
	observe := observeDeliveryPools(t, root, nodes)
	observe()
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	for _, node := range nodes {
		startCompetingMiner(t, node)
	}
	cancel := originals[39]
	if cancel.To() == nil || *cancel.To() != owners[0] || cancel.Value().Sign() != 0 || cancel.Gas() != 21000 || len(cancel.Data()) != 0 {
		t.Fatal("preserved abandonment is not the reviewed zero-value self-transfer")
	}
	if purchase := readPeerPurchase(t, nodes[0]); purchase.Nonce != 39 || !bytes.Equal(purchase.Saved, prior.Cold.Saved) || len(purchase.Pending)+len(purchase.Queued) != 0 {
		t.Fatal("buyer changed the retained gap before replay")
	}
	raw, err := cancel.MarshalBinary()
	requireNoError(t, err)
	var submitted common.Hash
	requireNoError(t, nodes[0].call(t, &submitted, "eth_sendRawTransaction", hexutil.Bytes(raw)))
	if submitted != cancel.Hash() {
		t.Fatal("abandonment replay changed identity")
	}
	receipt := awaitLiveFundingTransfer(t, nodes, cancel)
	if len(receipt.Logs) != 0 || receipt.BlockNumber.Uint64() <= prior.Final.Number.Uint64() {
		t.Fatal("replayed self-transfer must have a new canonical receipt without ticket creation")
	}
	awaitRehearsal(t, 5*time.Second, func() bool {
		purchase := readPeerPurchase(t, nodes[0])
		return purchase.Nonce == 40 && len(purchase.Pending)+len(purchase.Queued) == 0
	})
	if purchase := readPeerPurchase(t, nodes[0]); !bytes.Equal(purchase.Saved, prior.Cold.Saved) {
		t.Fatal("replayed abandonment changed the later saved purchase")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "abandonment-replayed.json"), map[string]interface{}{"Transaction": cancel, "Raw": hexutil.Bytes(raw), "Receipt": receipt, "After": readPeerPurchase(t, nodes[0])}))
	gap := livePurchaseGap{index: 0, nonce: 40, saved: &saved, head: types.NewBlockWithHeader(prior.Final)}
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
		if repair.OriginalsIncluded != 3 || repair.Successors < 2 || len(purchases[0]) < 6 || len(purchases[1]) < 3 || produced[0] == 0 || produced[1] == 0 || purchases[0][3].Hash() != saved.Hash() {
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
	var liveHeader *types.Header
	if live != nil {
		liveHeader = live.Header()
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "repair-result.json"), map[string]interface{}{"Before": prior.Final, "Live": liveHeader, "Final": final.Header(), "Repair": repair, "Abandonment": cancel, "AbandonmentReceipt": receipt, "Purchases": purchases, "ProducedThroughLive": produced, "NewFunding": false, "RecordEdits": false, "ResignedOriginals": false, "HeldSigner": false}))
	if repair.FundingFailure != "" {
		t.Fatalf("preserved rollback repair remains unfunded: %s", repair.FundingFailure)
	}
	t.Logf("exact abandonment and purchases 40-42 replayed; saved 43 and fresh successors executed; both producers resumed; purchases=%d/%d produced=%v final=%d %s", len(purchases[0]), len(purchases[1]), produced, final.NumberU64(), final.Hash().Hex())
}

func TestFullStateAbandonmentRepairColdAudit(t *testing.T) {
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
