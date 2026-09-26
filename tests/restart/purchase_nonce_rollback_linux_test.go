package restart

import (
	"bytes"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func rehearsePurchaseNonceRollback(t *testing.T) {
	localPath, localSeed, localSecond := seedTwoMinerPeer(t)
	remotePath, remoteFirst, remoteSeed := seedTwoMinerPeer(t)
	advanceTwoMinerFixture(t, localSeed, localSecond, remoteSeed)
	anchor := localSeed.chain.CurrentBlock()
	old := buildAnchorBranch(t, localSeed, 2, 120)
	original := old[0].Transactions()[0]
	last := old[1].Transactions()[0]
	encoded, err := last.MarshalBinary()
	requireNoError(t, err)
	requireNoError(t, localSeed.db.Put(append([]byte("fsn-auto-ticket-v1-"), localSeed.owner[:]...), encoded))
	var peerHead *types.Block
	for i := 0; i < 3; i++ {
		producer := preferredFixtureProducer(t, remoteFirst, remoteSeed)
		parent := remoteSeed.chain.CurrentBlock()
		purchase := remoteSeed.signPurchase(t, parent.Time(), common.TimeLockForever)
		peerHead = producer.buildBlockWithTransactions(t, parent.Time()+121, []*types.Transaction{purchase})
		remoteSeed.importBlock(t, peerHead)
	}
	if remoteSeed.chain.GetTd(peerHead.Hash(), peerHead.NumberU64()).Cmp(localSeed.chain.GetTd(old[1].Hash(), old[1].NumberU64())) <= 0 {
		t.Fatal("fixture peer is not heavier")
	}
	closeTwoMinerSeed(t, localPath, localSeed, anchor, 1)
	closeTwoMinerSeed(t, remotePath, remoteFirst, anchor, 2)
	local := startRehearsalNode(t, localPath)
	startHeldPurchaseWorker(t, local)
	before := awaitPeerPurchase(t, local, original.Nonce()+2)
	remote := startRehearsalNode(t, remotePath)
	syncRecoveryNode(t, local, remote, peerHead)
	awaitRehearsal(t, 10*time.Second, func() bool {
		var state peerPurchaseState
		requireNoError(t, local.call(t, &state, "lab_purchaseState"))
		return state.Nonce == original.Nonce() && len(state.Pending) == 1 && state.Pending[0].Hash() == original.Hash()
	})
	requirePausedPeerPurchase(t, local, before.Saved, original.Nonce(), original, peerHead)
	for _, tx := range []*types.Transaction{original, last} {
		var receipt *types.Receipt
		requireNoError(t, local.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
		if receipt != nil {
			t.Fatal("rolled-back purchase retained a canonical receipt")
		}
	}
	firstRecovery := minePeerPurchase(t, remote, original)
	syncRecoveryNode(t, local, remote, firstRecovery)
	requirePausedPeerPurchase(t, local, before.Saved, original.Nonce()+1, nil, firstRecovery)
	requireDisplacedPurchaseRPC(t, local, old[1], last)
	local.stop(t, false)
	requirePurchaseLogContains(t, localPath, "another ticket purchase")
	requirePurchaseLogContains(t, localPath, fmt.Sprintf("current nonce is %d", original.Nonce()+1))
	local = startRehearsalNode(t, localPath)
	startHeldPurchaseWorker(t, local)
	requirePausedPeerPurchase(t, local, before.Saved, original.Nonce()+1, nil, firstRecovery)
	retrieved := requireDisplacedPurchaseRPC(t, local, old[1], last)
	secondRecovery := minePeerPurchase(t, remote, retrieved)
	syncRecoveryNode(t, local, remote, secondRecovery)
	after := awaitPeerPurchase(t, local, original.Nonce()+2)
	if !bytes.Equal(after.Saved, before.Saved) {
		t.Fatal("nonce repair changed the retained successor's signed bytes")
	}
	requirePeerPurchaseStable(t, local, after.Saved, original.Nonce()+2, secondRecovery)
	t.Logf("two-block live peer rollback nonce %d -> %d; only lowest displaced ticket was reinjected; missing nonce paused across cold restart; ordinary raw resubmission/mining restored nonce %d and exact saved successor", original.Nonce()+2, original.Nonce(), after.Nonce)
}

func preferredFixtureProducer(t *testing.T, first, second *fixture) *fixture {
	t.Helper()
	parent := first.chain.CurrentBlock()
	state, err := first.chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	for _, candidate := range []*fixture{first, second} {
		if tickets.NumberOfTicketsByAddress(candidate.owner) == 0 {
			continue
		}
		header := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number(), big.NewInt(1)), Coinbase: candidate.owner, Time: parent.Time() + 121}
		requireNoError(t, candidate.engine.Prepare(candidate.chain, header))
		if header.Nonce.Uint64() == 0 {
			return candidate
		}
	}
	t.Fatal("two-owner fixture has no first-ranked eligible producer")
	return nil
}

func requirePausedPeerPurchase(t *testing.T, node *rehearsalNode, saved []byte, nonce uint64, pending *types.Transaction, head *types.Block) {
	t.Helper()
	deadline := time.Now().Add(6 * time.Second)
	for time.Now().Before(deadline) {
		var state peerPurchaseState
		requireNoError(t, node.call(t, &state, "lab_purchaseState"))
		if !bytes.Equal(state.Saved, saved) || state.Nonce != nonce || len(state.Queued) != 0 {
			t.Fatalf("paused purchase changed: nonce=%d pending=%d queued=%d", state.Nonce, len(state.Pending), len(state.Queued))
		}
		if pending == nil && len(state.Pending) != 0 || pending != nil && (len(state.Pending) != 1 || state.Pending[0].Hash() != pending.Hash()) {
			t.Fatalf("unexpected reinjected pool contents: %+v", state.Pending)
		}
		requireRehearsalHead(t, node.status(t), head)
		time.Sleep(100 * time.Millisecond)
	}
}

func minePeerPurchase(t *testing.T, node *rehearsalNode, tx *types.Transaction) *types.Block {
	t.Helper()
	data, err := tx.MarshalBinary()
	requireNoError(t, err)
	var hash common.Hash
	err = node.call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(data))
	if err != nil && !strings.Contains(err.Error(), "already known") {
		t.Fatal(err)
	}
	requireNoError(t, node.call(t, nil, "miner_start", 1))
	var receipt *types.Receipt
	awaitRehearsal(t, 45*time.Second, func() bool {
		requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
		return receipt != nil
	})
	requireNoError(t, node.call(t, nil, "miner_stop"))
	if receipt.Status != types.ReceiptStatusSuccessful {
		t.Fatal("resubmitted native purchase failed")
	}
	block := readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64())
	if block.Hash() != receipt.BlockHash {
		t.Fatal("resubmitted purchase receipt is not canonical")
	}
	owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
	requireNoError(t, err)
	requirePeerNativePurchase(t, receipt, block, tx, owner)
	return block
}

func requirePurchaseLogContains(t *testing.T, path, expected string) {
	t.Helper()
	files, err := filepath.Glob(filepath.Join(path, "process-*.log"))
	requireNoError(t, err)
	for _, file := range files {
		data, err := os.ReadFile(file)
		requireNoError(t, err)
		if strings.Contains(string(data), expected) {
			return
		}
	}
	t.Fatalf("node did not log %q", expected)
}
