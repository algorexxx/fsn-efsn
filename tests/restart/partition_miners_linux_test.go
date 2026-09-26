package restart

import (
	"bytes"
	"math/big"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func rehearsePartitionPurchaseMiners(t *testing.T) {
	requirePartitionNamespace(t)
	firstPath, firstSeed, secondSigner := seedTwoMinerPeer(t)
	secondPath, secondSeed, _ := seedTwoMinerPeer(t)
	advanceTwoMinerFixture(t, firstSeed, secondSigner, secondSeed)
	anchor := firstSeed.chain.CurrentBlock()
	owners := []common.Address{firstSeed.owner, secondSigner.owner}
	closeTwoMinerSeed(t, firstPath, firstSeed, anchor, 1)
	closeTwoMinerSeed(t, secondPath, secondSeed, anchor, 2)
	first := startRehearsalNode(t, firstPath)
	second := startRehearsalNode(t, secondPath)
	connectRehearsalPeer(t, first, second)
	awaitMinerPartitionPeers(t, first, second, 1, 5*time.Second)
	for _, node := range []*rehearsalNode{first, second} {
		requireRehearsalHead(t, node.status(t), anchor)
		if readPeerPurchase(t, node).Nonce != 14 {
			t.Fatal("expected fourteen fixture purchases before the network fault")
		}
	}
	heal := dropRehearsalPackets(t, "match", "ip", "dst", "127.0.0.0/8")
	cut := time.Now()
	startCompetingMiner(t, first)
	startCompetingMiner(t, second)
	ready := [2]bool{}
	nodes := []*rehearsalNode{first, second}
	awaitRehearsal(t, 60*time.Second, func() bool {
		for i, node := range nodes {
			if !ready[i] && readPeerPurchase(t, node).Nonce > 14 {
				stopPeerAutoMiner(t, node)
				ready[i] = true
			}
		}
		return ready[0] && ready[1]
	})
	awaitMinerPartitionPeers(t, first, second, 0, 45*time.Second)
	if remaining := 45*time.Second - time.Since(cut); remaining > 0 {
		time.Sleep(remaining)
	}
	blocks := make([]*types.Block, 2)
	purchaseBlocks := make([]*types.Block, 2)
	purchases := make([]*types.Transaction, 2)
	for i, node := range nodes {
		head := node.status(t)
		if readPeerPurchase(t, node).Nonce != 15 || head.Number < anchor.NumberU64()+1 || head.Number > anchor.NumberU64()+3 {
			t.Fatalf("bounded partition must produce one to three blocks and exactly one purchase per owner: height=%d nonce=%d", head.Number, readPeerPurchase(t, node).Nonce)
		}
		blocks[i] = readRecoveryNodeBlock(t, node, anchor.NumberU64()+1)
		if blocks[i].ParentHash() != anchor.Hash() || blocks[i].Coinbase() != owners[i] {
			t.Fatal("isolated worker did not extend the shared anchor with its own key")
		}
		for number := anchor.NumberU64() + 1; number <= head.Number; number++ {
			block := readRecoveryNodeBlock(t, node, number)
			for _, tx := range block.Transactions() {
				if !tx.IsBuyTicketTx() {
					continue
				}
				owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
				requireNoError(t, err)
				if owner == owners[i] {
					purchases[i], purchaseBlocks[i] = tx, block
					requirePartitionPurchaseReceipt(t, node, block, tx, owner)
				}
			}
		}
		if purchases[i] == nil {
			t.Fatal("isolated worker omitted its own native purchase")
		}
	}
	if blocks[0].Hash() == blocks[1].Hash() || (*big.Int)(first.status(t).TD).Cmp((*big.Int)(second.status(t).TD)) == 0 {
		t.Fatal("independent workers must create distinct branches with unequal ordinary difficulty")
	}
	winner, loser := orderPeerDifficulty(t, first, second)
	joined := readRecoveryNodeBlock(t, winner, winner.status(t).Number)
	t.Logf("connected miners partitioned for %s; isolated blocks %s / %s, TD %s / %s; both sessions gone", time.Since(cut), blocks[0].Hash().Hex(), blocks[1].Hash().Hex(), (*big.Int)(first.status(t).TD), (*big.Int)(second.status(t).TD))
	heal()
	healed := time.Now()
	awaitMinerPartitionPeers(t, first, second, 1, 90*time.Second)
	awaitRehearsal(t, 30*time.Second, func() bool { return loser.status(t).Hash == joined.Hash() })
	for i, node := range nodes {
		requireRehearsalHead(t, node.status(t), joined)
		for j, tx := range purchases {
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if nodes[j] == winner {
				requirePeerNativePurchase(t, receipt, purchaseBlocks[j], tx, owners[j])
			} else if receipt != nil {
				t.Fatalf("node %d retained the displaced purchase receipt", i)
			}
		}
	}
	t.Logf("automatic static reconnect and normal sync converged in %s to %d %s; canonical receipts agree", time.Since(healed), joined.NumberU64(), joined.Hash().Hex())
	startCompetingMiner(t, first)
	startCompetingMiner(t, second)
	awaitRehearsal(t, 90*time.Second, func() bool {
		return first.status(t).Number >= joined.NumberU64()+3 && readPeerPurchase(t, first).Nonce >= 16 && readPeerPurchase(t, second).Nonce >= 16
	})
	stopPeerAutoMiner(t, first)
	stopPeerAutoMiner(t, second)
	final := awaitStoppedPartitionHead(t, first, second)
	counts := make(map[common.Address]int)
	for number := anchor.NumberU64() + 1; number <= final.NumberU64(); number++ {
		block := readRecoveryNodeBlock(t, winner, number)
		for _, tx := range block.Transactions() {
			if !tx.IsBuyTicketTx() {
				continue
			}
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			for _, node := range nodes {
				requirePartitionPurchaseReceipt(t, node, block, tx, owner)
			}
			counts[owner]++
		}
	}
	if counts[owners[0]] < 2 || counts[owners[1]] < 2 {
		t.Fatalf("both owners must purchase on the common chain after healing: %v", counts)
	}
	for i, node := range nodes {
		requireRehearsalHead(t, node.status(t), final)
		var receipt *types.Receipt
		requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", purchases[i].Hash()))
		if receipt == nil {
			t.Fatal("original isolated purchase was not recovered on the common chain")
		}
		startHeldPurchaseWorker(t, node)
		nonce := readPeerPurchase(t, node).Nonce
		saved := awaitPeerPurchase(t, node, nonce)
		requirePeerPurchaseStable(t, node, saved.Saved, nonce, final)
		node.stop(t, false)
		cold := startRehearsalNode(t, node.path)
		requireRehearsalHead(t, cold.status(t), final)
		restored := readPeerPurchase(t, cold)
		if !bytes.Equal(restored.Saved, saved.Saved) || restored.Nonce != nonce || len(restored.Pending)+len(restored.Queued) != 0 {
			t.Fatal("cold restart did not preserve intent and canonical nonce with an empty pool")
		}
		startHeldPurchaseWorker(t, cold)
		recovered := awaitPeerPurchase(t, cold, nonce)
		if !bytes.Equal(recovered.Saved, saved.Saved) {
			t.Fatal("cold purchase recovery changed the saved signed bytes")
		}
		requirePeerPurchaseStable(t, cold, saved.Saved, nonce, final)
	}
	t.Logf("packet-loss miner recovery passed: final %d %s state=%s tickets=%s purchases key1=%d key2=%d; both cold heads and exact saved intents agree", final.NumberU64(), final.Hash().Hex(), final.Root().Hex(), final.MixDigest().Hex(), counts[owners[0]], counts[owners[1]])
}

func awaitStoppedPartitionHead(t *testing.T, first, second *rehearsalNode) *types.Block {
	t.Helper()
	previous := [2]common.Hash{first.status(t).Hash, second.status(t).Hash}
	quiet := time.Now()
	changes := 0
	awaitRehearsal(t, 90*time.Second, func() bool {
		for i, node := range []*rehearsalNode{first, second} {
			status := node.status(t)
			if status.Mining || status.AutoBuy {
				t.Fatal("miner and automatic buyer must remain disabled while observing pending seals")
			}
			if status.Hash != previous[i] {
				previous[i], quiet = status.Hash, time.Now()
				changes++
			}
		}
		return previous[0] == previous[1] && time.Since(quiet) >= 35*time.Second
	})
	block := readRecoveryNodeBlock(t, first, first.status(t).Number)
	t.Logf("stopped miners reached a common head unchanged for 35s; observed %d head changes after stop; final %d %s", changes, block.NumberU64(), block.Hash().Hex())
	return block
}

func awaitMinerPartitionPeers(t *testing.T, first, second *rehearsalNode, want uint64, timeout time.Duration) {
	t.Helper()
	awaitRehearsal(t, timeout, func() bool {
		for _, node := range []*rehearsalNode{first, second} {
			var peers hexutil.Uint64
			requireNoError(t, node.call(t, &peers, "net_peerCount"))
			if uint64(peers) != want {
				return false
			}
		}
		return true
	})
}

func requirePartitionPurchaseReceipt(t *testing.T, node *rehearsalNode, block *types.Block, tx *types.Transaction, owner common.Address) {
	t.Helper()
	var receipt *types.Receipt
	requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
	requirePeerNativePurchase(t, receipt, block, tx, owner)
}
