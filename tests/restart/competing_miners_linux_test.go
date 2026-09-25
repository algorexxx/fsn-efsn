package restart

import (
	"encoding/json"
	"math/big"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func rehearseCompetingPurchaseMiners(t *testing.T) {
	firstPath, firstSeed, secondSigner := seedTwoMinerPeer(t)
	secondPath, secondSeed, _ := seedTwoMinerPeer(t)
	advanceTwoMinerFixture(t, firstSeed, secondSigner, secondSeed)
	anchor := firstSeed.chain.CurrentBlock()
	owners := []common.Address{firstSeed.owner, secondSigner.owner}
	closeTwoMinerSeed(t, firstPath, firstSeed, anchor, 1)
	closeTwoMinerSeed(t, secondPath, secondSeed, anchor, 2)
	first := startRehearsalNode(t, firstPath)
	second := startRehearsalNode(t, secondPath)
	startCompetingMiner(t, first)
	startCompetingMiner(t, second)
	firstReady, secondReady := false, false
	awaitRehearsal(t, 60*time.Second, func() bool {
		if !firstReady && readPeerPurchase(t, first).Nonce > 14 {
			stopPeerAutoMiner(t, first)
			firstReady = true
		}
		if !secondReady && readPeerPurchase(t, second).Nonce > 14 {
			stopPeerAutoMiner(t, second)
			secondReady = true
		}
		return firstReady && secondReady
	})
	before := []peerPurchaseState{readPeerPurchase(t, first), readPeerPurchase(t, second)}
	if before[0].Nonce != 15 || before[1].Nonce != 15 {
		t.Fatal("partition phase must include exactly one purchase per owner")
	}
	firstBlock := readRecoveryNodeBlock(t, first, anchor.NumberU64()+1)
	secondBlock := readRecoveryNodeBlock(t, second, anchor.NumberU64()+1)
	if firstBlock.Hash() == secondBlock.Hash() || firstBlock.ParentHash() != anchor.Hash() || secondBlock.ParentHash() != anchor.Hash() || firstBlock.Coinbase() != owners[0] || secondBlock.Coinbase() != owners[1] {
		t.Fatal("distinct real workers did not produce competing descendants of the anchor")
	}
	if (*big.Int)(first.status(t).TD).Cmp((*big.Int)(second.status(t).TD)) == 0 {
		old := first.status(t).Number
		startCompetingMiner(t, first)
		awaitRehearsal(t, 45*time.Second, func() bool { return first.status(t).Number > old })
		stopPeerAutoMiner(t, first)
	}
	winner, loser := orderPeerDifficulty(t, first, second)
	joined := readRecoveryNodeBlock(t, winner, winner.status(t).Number)
	syncRecoveryNode(t, loser, winner, joined)
	startCompetingMiner(t, first)
	startCompetingMiner(t, second)
	awaitRehearsal(t, 75*time.Second, func() bool {
		return first.status(t).Number >= joined.NumberU64()+3 &&
			readPeerPurchase(t, first).Nonce > before[0].Nonce && readPeerPurchase(t, second).Nonce > before[1].Nonce
	})
	stopPeerAutoMiner(t, first)
	stopPeerAutoMiner(t, second)
	winner, loser = orderPeerDifficulty(t, first, second)
	final := readRecoveryNodeBlock(t, winner, winner.status(t).Number)
	if loser.status(t).Hash != final.Hash() {
		syncRecoveryNode(t, loser, winner, final)
	}
	counts := make(map[common.Address]int)
	for number := anchor.NumberU64() + 1; number <= final.NumberU64(); number++ {
		block := readRecoveryNodeBlock(t, winner, number)
		for _, tx := range block.Transactions() {
			if !tx.IsBuyTicketTx() {
				continue
			}
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			var receipt *types.Receipt
			requireNoError(t, winner.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			requirePeerNativePurchase(t, receipt, block, tx, owner)
			counts[owner]++
		}
	}
	if counts[owners[0]] < 2 || counts[owners[1]] < 2 {
		t.Fatalf("both owners must buy again on the converged chain: %v", counts)
	}
	for _, node := range []*rehearsalNode{first, second} {
		nonce := readPeerPurchase(t, node).Nonce
		startHeldPurchaseWorker(t, node)
		purchase := awaitPeerPurchase(t, node, nonce)
		requirePeerPurchaseStable(t, node, purchase.Saved, nonce, final)
	}
	t.Logf("distinct live worker forks %s / %s joined at %d, continued to %d %s; native purchases key1=%d key2=%d; both persisted heads, roots and next-nonce records/pools agree", firstBlock.Hash().Hex(), secondBlock.Hash().Hex(), joined.NumberU64(), final.NumberU64(), final.Hash().Hex(), counts[owners[0]], counts[owners[1]])
}

func readPeerPurchase(t *testing.T, node *rehearsalNode) peerPurchaseState {
	t.Helper()
	var state peerPurchaseState
	requireNoError(t, node.call(t, &state, "lab_purchaseState"))
	return state
}

func stopPeerAutoMiner(t *testing.T, node *rehearsalNode) {
	t.Helper()
	requireNoError(t, node.call(t, nil, "miner_stopAutoBuyTicket"))
	requireNoError(t, node.call(t, nil, "miner_stop"))
	awaitRehearsal(t, 10*time.Second, func() bool { return !node.status(t).Mining })
}

func startCompetingMiner(t *testing.T, node *rehearsalNode) {
	t.Helper()
	requireNoError(t, node.call(t, nil, "miner_start", 1))
	awaitRehearsal(t, 20*time.Second, func() bool { return node.status(t).Mining })
	requireNoError(t, node.call(t, nil, "miner_startAutoBuyTicket"))
}

func orderPeerDifficulty(t *testing.T, first, second *rehearsalNode) (*rehearsalNode, *rehearsalNode) {
	t.Helper()
	if (*big.Int)(first.status(t).TD).Cmp((*big.Int)(second.status(t).TD)) >= 0 {
		return first, second
	}
	return second, first
}

func requirePeerNativePurchase(t *testing.T, receipt *types.Receipt, block *types.Block, tx *types.Transaction, owner common.Address) {
	t.Helper()
	if receipt == nil || receipt.Status != types.ReceiptStatusSuccessful || receipt.TxHash != tx.Hash() || receipt.BlockHash != block.Hash() {
		t.Fatal("native purchase has no successful canonical receipt")
	}
	parent := block.ParentHash()
	id := crypto.Keccak256Hash(owner[:], parent[:])
	for _, entry := range receipt.Logs {
		if entry.Address != common.FSNCallAddress || len(entry.Topics) == 0 || entry.Topics[0] != common.BytesToHash([]byte{byte(common.BuyTicketFunc)}) {
			continue
		}
		var result struct {
			TicketID    common.Hash
			TicketOwner common.Address
			Error       string
		}
		requireNoError(t, json.Unmarshal(entry.Data, &result))
		if result.Error == "" && result.TicketID == id && result.TicketOwner == owner {
			return
		}
	}
	t.Fatal("receipt lacks the expected successful native ticket result")
}
