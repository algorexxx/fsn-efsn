package restart

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestFullStateFundingLiveContinuation(t *testing.T) {
	rehearseFullStateFundingLive(t, false)
}

func TestFullStateFundingStartOrder(t *testing.T) {
	rehearseFullStateFundingLive(t, true)
}

func rehearseFullStateFundingLive(t *testing.T, minersFirst bool) {
	t.Helper()
	root := os.Getenv("FUSION_RESTART_FUNDING_LIVE")
	if root == "" {
		t.Skip("requires the completed controlled funding recovery")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	var recovery struct {
		Final          *types.Header
		Contributions  types.Transactions
		SavedPurchases [2]*types.Transaction
	}
	readHandoverJSON(t, filepath.Join(root, "funding-recovery.json"), &recovery)
	var cleanup fullStateBlockLedger
	readHandoverJSON(t, filepath.Join(root, "blocks", "block-03.json"), &cleanup)
	anchor := types.NewBlockWithHeader(cleanup.Header)
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 5*time.Minute)}
	owners := [2]common.Address{common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
	var before [2]peerPurchaseState
	for i, node := range nodes {
		requireRehearsalHead(t, node.status(t), types.NewBlockWithHeader(recovery.Final))
		purchase := readPeerPurchase(t, node)
		expected, err := recovery.SavedPurchases[i].MarshalBinary()
		requireNoError(t, err)
		if minersFirst {
			expected = nil
			if i == 1 {
				var ready peerPurchaseState
				readHandoverJSON(t, filepath.Join(root, "live-ready-purchase.json"), &ready)
				expected = ready.Saved
			}
		}
		if !bytes.Equal(purchase.Saved, expected) || purchase.Nonce != []uint64{8, 13}[i] || len(purchase.Pending)+len(purchase.Queued) != 0 {
			t.Fatal("prior result did not reopen with the exact saved bytes and canonical nonce")
		}
		before[i] = purchase
	}
	if minersFirst {
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "retry-before-purchases.json"), before))
	}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	if minersFirst {
		for _, node := range nodes {
			requireNoError(t, node.call(t, nil, "miner_start", 1))
			awaitRehearsal(t, 20*time.Second, func() bool { return node.status(t).Mining })
		}
		requireNoError(t, nodes[1].call(t, nil, "miner_startAutoBuyTicket"))
	} else {
		startCompetingMiner(t, nodes[1])
	}
	var pending peerPurchaseState
	awaitRehearsal(t, 30*time.Second, func() bool {
		pending = readPeerPurchase(t, nodes[1])
		if len(pending.Saved) == 0 || len(pending.Pending) != 1 || len(pending.Queued) != 0 {
			return false
		}
		var next types.Transaction
		requireNoError(t, next.UnmarshalBinary(pending.Saved))
		return next.Nonce() == 13 && pending.Pending[0].Hash() == next.Hash()
	})
	if minersFirst {
		if !bytes.Equal(pending.Saved, before[1].Saved) {
			t.Fatal("ordered restart replaced the failed attempt's saved purchase")
		}
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "retry-ready-purchase.json"), pending))
		requireNoError(t, nodes[0].call(t, nil, "miner_startAutoBuyTicket"))
		t.Log("funding continuation started both miners before either buyer; exact pending entrant nonce 13 resubmitted automatically after ordinary restart")
	} else {
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "live-ready-purchase.json"), pending))
		if nodes[1].status(t).Signatures != 0 || nodes[0].status(t).Hash != recovery.Final.Hash() {
			t.Fatal("zero-ticket entrant unexpectedly signed or advanced the chain before staging")
		}
		t.Log("funding live continuation staged entrant automatic nonce 13 in the real pool before enabling the donation's sole remaining ticket")
		startCompetingMiner(t, nodes[0])
	}
	progress := awaitContinuousMinerProgress(t, nodes[0], nodes[1], owners, [2]uint64{9, 14}, recovery.Final.Number.Uint64(), 150*time.Second)
	t.Logf("funding live continuation reached two fresh automatic purchases per owner; common=%d %s", progress.NumberU64(), progress.Hash().Hex())
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		requireRehearsalHead(t, node.status(t), final)
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "live-stopped-purchases.json"), stopped))
	artifacts := filepath.Join(root, "live-blocks")
	count := captureFullStateColdSuffixAt(t, root, final, artifacts)
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	if len(recovery.Contributions) != 2 {
		t.Fatal("controlled contribution manifest differs")
	}
	allowed := make(map[common.Hash]uint64)
	for _, tx := range recovery.Contributions {
		allowed[tx.Hash()] = recovery.Final.Number.Uint64() - 1
	}
	auditFullStateParticipantTransfers(t, artifacts, count, allowed)
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("cold-intent-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			state, err := f.chain.State()
			requireNoError(t, err)
			key := append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...)
			exists, err := f.db.Has(key)
			requireNoError(t, err)
			if exists != (len(stopped[i].Saved) > 0) || state.GetNonce(owners[i]) != stopped[i].Nonce {
				t.Fatal("cold saved record presence or canonical nonce differs")
			}
			if exists {
				saved, err := f.db.Get(key)
				requireNoError(t, err)
				if !bytes.Equal(saved, stopped[i].Saved) {
					t.Fatal("cold saved intent bytes changed")
				}
			}
			recordFundingInventory(t, root, role+"-live-final", f, append([]common.Address{f.owner}, owners[:]...), recovery.SavedPurchases)
		}) {
			t.Fatal("live funding continuation cold verification failed")
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "live-funding-result.json"), map[string]interface{}{"Before": recovery.Final, "Final": final.Header(), "Blocks": count, "RequiredFreshNonces": []uint64{9, 14}, "PartitionExercised": false, "NonceGapExercised": false}))
	t.Log("complete-state funding live continuation passed: exact saved intents reconciled, both buyers made at least two fresh purchases, both cold ledgers and saved records agree; no partition or nonce rollback exercised")
}
