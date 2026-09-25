package restart

import (
	"bytes"
	"errors"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/syndtr/goleveldb/leveldb"
)

type peerPurchaseState struct {
	Nonce   uint64
	Saved   hexutil.Bytes
	Pending types.Transactions
	Queued  types.Transactions
}

func (a *nodeRehearsalAPI) PurchaseState() (peerPurchaseState, error) {
	owner, err := a.service.Etherbase()
	if err != nil {
		return peerPurchaseState{}, err
	}
	state, err := a.service.BlockChain().State()
	if err != nil {
		return peerPurchaseState{}, err
	}
	data, err := a.service.ChainDb().Get(append([]byte("fsn-auto-ticket-v1-"), owner[:]...))
	if err != nil && !errors.Is(err, leveldb.ErrNotFound) {
		return peerPurchaseState{}, err
	}
	pending, queued := a.service.TxPool().Content()
	return peerPurchaseState{Nonce: state.GetNonce(owner), Saved: data, Pending: pending[owner], Queued: queued[owner]}, state.Error()
}

func (a *nodeRehearsalAPI) HoldWorker() error {
	owner, err := a.service.Etherbase()
	if err != nil {
		return err
	}
	a.service.Engine().(*datong.DaTong).Authorize(owner, func(accounts.Account, string, []byte) ([]byte, error) {
		return nil, errors.New("public peer fixture deliberately withholds block signatures")
	})
	a.service.Miner().Start(owner)
	return nil
}

func rehearsePurchasePeer(t *testing.T, replace bool) {
	localPath, localSeed := seedPurchasePeer(t)
	remotePath, remoteSeed := seedPurchasePeer(t)
	advancePurchaseFixture(t, localSeed, remoteSeed)
	anchor := localSeed.chain.CurrentBlock()
	original := localSeed.signPurchase(t, anchor.Time(), common.TimeLockForever)
	oldHead := localSeed.buildBlockWithTransactions(t, anchor.Time()+120, []*types.Transaction{original})
	localSeed.importBlock(t, oldHead)
	encoded, err := original.MarshalBinary()
	requireNoError(t, err)
	requireNoError(t, localSeed.db.Put(append([]byte("fsn-auto-ticket-v1-"), localSeed.owner[:]...), encoded))
	transactions := []*types.Transaction{original}
	if replace {
		transfer, err := types.SignTx(types.NewTransaction(original.Nonce(), localSeed.owner, new(big.Int), 21000, original.GasPrice(), nil), types.LatestSigner(localSeed.chain.Config()), localSeed.key)
		requireNoError(t, err)
		purchase, err := types.SignTx(types.NewTransaction(original.Nonce()+1, *original.To(), original.Value(), original.Gas(), original.GasPrice(), original.Data()), types.LatestSigner(localSeed.chain.Config()), localSeed.key)
		requireNoError(t, err)
		transactions = []*types.Transaction{transfer, purchase}
	}
	first := remoteSeed.buildBlockWithTransactions(t, anchor.Time()+121, transactions)
	remoteSeed.importBlock(t, first)
	final := buildAnchorBranch(t, remoteSeed, 1, 121)[0]
	closeRehearsalSeed(t, localPath, localSeed, anchor)
	closeRehearsalSeed(t, remotePath, remoteSeed, anchor)
	local := startRehearsalNode(t, localPath)
	startHeldPurchaseWorker(t, local)
	before := awaitPeerPurchase(t, local, original.Nonce()+1)
	var successor types.Transaction
	requireNoError(t, successor.UnmarshalBinary(before.Saved))
	requireRehearsalHead(t, local.status(t), oldHead)
	remote := startRehearsalNode(t, remotePath)
	if (*big.Int)(remote.status(t).TD).Cmp((*big.Int)(local.status(t).TD)) <= 0 {
		t.Fatal("peer branch must have greater total difficulty")
	}
	syncRecoveryNode(t, local, remote, final)
	nonce := original.Nonce() + 2
	if replace {
		nonce++
	}
	after := awaitPeerPurchase(t, local, nonce)
	var recovered types.Transaction
	requireNoError(t, recovered.UnmarshalBinary(after.Saved))
	if recovered.Hash() == successor.Hash() {
		t.Fatal("consumed successor remained the automatic intent")
	}
	var receipt *types.Receipt
	requireNoError(t, local.call(t, &receipt, "eth_getTransactionReceipt", original.Hash()))
	if replace {
		if receipt != nil {
			t.Fatal("replaced purchase retained a canonical receipt")
		}
	} else if receipt == nil || receipt.BlockHash != first.Hash() || receipt.Status != types.ReceiptStatusSuccessful {
		t.Fatal("re-included purchase receipt did not move to the peer's block")
	}
	receipt = nil
	requireNoError(t, local.call(t, &receipt, "eth_getTransactionReceipt", successor.Hash()))
	if receipt != nil {
		t.Fatal("unmined successor acquired a false receipt")
	}
	requirePeerPurchaseStable(t, local, after.Saved, nonce, final)
	local.stop(t, false)
	requirePeerPurchaseLogs(t, localPath)
	reopened := startRehearsalNode(t, localPath)
	var emptyPool peerPurchaseState
	requireNoError(t, reopened.call(t, &emptyPool, "lab_purchaseState"))
	if !bytes.Equal(emptyPool.Saved, after.Saved) || len(emptyPool.Pending)+len(emptyPool.Queued) != 0 || emptyPool.Nonce != nonce {
		t.Fatal("cold process did not retain the record with an initially empty pool")
	}
	startHeldPurchaseWorker(t, reopened)
	cold := awaitPeerPurchase(t, reopened, nonce)
	if !bytes.Equal(cold.Saved, after.Saved) {
		t.Fatal("cold restart changed the surviving signed purchase")
	}
	requirePeerPurchaseStable(t, reopened, cold.Saved, nonce, final)
	t.Logf("real peer reorganization replace=%t: ancestor=%d old=%s new=%s; original nonce=%d retired successor=%s current=%s nonce=%d; receipt lookup, pool and cold recovery agree", replace, anchor.NumberU64(), oldHead.Hash().Hex(), final.Hash().Hex(), original.Nonce(), successor.Hash().Hex(), recovered.Hash().Hex(), nonce)
}

func seedPurchasePeer(t *testing.T) (string, *fixture) {
	t.Helper()
	path, err := os.MkdirTemp("", "fsn-purchase-peer-")
	requireNoError(t, err)
	t.Cleanup(func() { os.RemoveAll(path) })
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "anchor-lab", "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	return path, newFixtureInDatabase(t, common.TimeLockForever, db)
}

func requirePeerPurchaseLogs(t *testing.T, path string) {
	t.Helper()
	files, err := filepath.Glob(filepath.Join(path, "process-*.log"))
	requireNoError(t, err)
	if len(files) != 1 {
		t.Fatal("expected the original node process log")
	}
	data, err := os.ReadFile(files[0])
	requireNoError(t, err)
	for message, count := range map[string]int{
		"Automatic ticket purchase confirmed":                          1,
		"Automatic ticket nonce consumed without a confirmed purchase": 1,
		"Automatic ticket submitted; awaiting inclusion":               2,
	} {
		if actual := strings.Count(string(data), message); actual != count {
			t.Fatalf("%q logged %d times, expected %d", message, actual, count)
		}
	}
}

func startHeldPurchaseWorker(t *testing.T, node *rehearsalNode) {
	t.Helper()
	requireNoError(t, node.call(t, nil, "lab_holdWorker"))
	awaitRehearsal(t, 5*time.Second, func() bool { return node.status(t).Mining })
	requireNoError(t, node.call(t, nil, "miner_startAutoBuyTicket"))
}

func awaitPeerPurchase(t *testing.T, node *rehearsalNode, nonce uint64) peerPurchaseState {
	t.Helper()
	var state peerPurchaseState
	awaitRehearsal(t, 15*time.Second, func() bool {
		requireNoError(t, node.call(t, &state, "lab_purchaseState"))
		if state.Nonce != nonce || len(state.Saved) == 0 || len(state.Pending) != 1 || len(state.Queued) != 0 {
			return false
		}
		var tx types.Transaction
		requireNoError(t, tx.UnmarshalBinary(state.Saved))
		return tx.Nonce() == nonce && tx.Hash() == state.Pending[0].Hash()
	})
	return state
}

func requirePeerPurchaseStable(t *testing.T, node *rehearsalNode, encoded []byte, nonce uint64, head *types.Block) {
	t.Helper()
	deadline := time.Now().Add(6 * time.Second)
	for time.Now().Before(deadline) {
		var state peerPurchaseState
		requireNoError(t, node.call(t, &state, "lab_purchaseState"))
		if !bytes.Equal(state.Saved, encoded) || state.Nonce != nonce || len(state.Pending) != 1 || len(state.Queued) != 0 {
			t.Fatal("purchase record, nonce or pool changed during retry interval")
		}
		pooled, err := state.Pending[0].MarshalBinary()
		requireNoError(t, err)
		if !bytes.Equal(pooled, encoded) {
			t.Fatal("pool and automatic record disagree")
		}
		requireRehearsalHead(t, node.status(t), head)
		time.Sleep(100 * time.Millisecond)
	}
}
