package restart

import (
	"context"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/accounts/keystore"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/event"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/miner"
)

func TestAutoBuyRuntime(t *testing.T) {
	if os.Getenv("FUSION_RESTART_AUTOBUY_CHILD") == "1" {
		runAutoBuyRuntime(t)
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 65*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestAutoBuyRuntime$", "-test.v", "-test.timeout=60s")
	command.Env = append(os.Environ(), "FUSION_RESTART_AUTOBUY_CHILD=1")
	output, err := command.CombinedOutput()
	t.Logf("isolated auto-buy runtime:\n%s", output)
	requireNoError(t, err)
}

func runAutoBuyRuntime(t *testing.T) {
	f := newFixture(t)
	verifier := newFixture(t)
	advancePurchaseFixture(t, f, verifier)
	initial := f.chain.CurrentBlock()
	statedb, err := f.chain.State()
	requireNoError(t, err)
	tickets, err := statedb.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTickets() != 1 {
		t.Fatal("runtime fixture must have exactly one surviving ticket")
	}
	keys := keystore.NewKeyStore(t.TempDir(), keystore.LightScryptN, keystore.LightScryptP)
	account, err := keys.ImportECDSA(f.key, "synthetic-test-key")
	requireNoError(t, err)
	requireNoError(t, keys.Unlock(account, "synthetic-test-key"))
	manager := accounts.NewManager(keys)
	t.Cleanup(func() { manager.Close() })
	b := &autoBuyBackend{purchaseBackend: &purchaseBackend{chain: f.chain}, pool: f.newPool(t), accounts: manager, owner: f.owner, database: f.db, submissions: make(chan purchaseSubmission, 8), initialized: make(chan struct{}, 1)}
	f.engine.Authorize(f.owner, func(_ accounts.Account, _ string, data []byte) ([]byte, error) {
		return crypto.Sign(crypto.Keccak256(data), f.key)
	})
	mux := new(event.TypeMux)
	b.miner = miner.New(b, &miner.Config{GasCeil: initial.GasLimit(), GasPrice: big.NewInt(1), Recommit: time.Second}, f.chain.Config(), mux, f.engine, func(block *types.Block) bool { return block.Coinbase() == f.owner })
	var closeMiner sync.Once
	t.Cleanup(func() { closeMiner.Do(b.miner.Close); mux.Stop() })
	lock := new(ethapi.AddrLocker)
	ethapi.NewFusionTransactionAPI(b, lock, ethapi.NewPublicTransactionPoolAPI(b, lock))
	heads := make(chan core.ChainHeadEvent, 8)
	subscription := f.chain.SubscribeChainHeadEvent(heads)
	t.Cleanup(subscription.Unsubscribe)
	b.miner.Start(f.owner)
	b.failNext.Store(true)
	confirmations := capturePurchaseLog(t, "Automatic ticket purchase confirmed")
	stopPurchases := startPurchaseController(t, true)
	select {
	case <-b.initialized:
	case <-time.After(5 * time.Second):
		t.Fatal("auto-buy did not initialize")
	}
	failed := awaitSubmission(t, b)
	requireErrorContains(t, failed.err, "injected temporary submission failure")
	if f.chain.CurrentBlock().Hash() != initial.Hash() {
		t.Fatal("failed submission unexpectedly advanced the chain")
	}
	retried := awaitSubmission(t, b)
	requireNoError(t, retried.err)
	hash := failed.tx.Hash()
	if retried.tx.Hash() != hash {
		t.Fatal("automatic retry changed the saved signed transaction")
	}
	first := awaitHead(t, heads)
	t.Logf("startup and automatic retry: identical tx=%s mined at height=%d", hash.Hex(), first.NumberU64())
	automatic := awaitSubmission(t, b)
	requireNoError(t, automatic.err)
	awaitPurchaseWarning(t, confirmations, fmt.Sprint(hash))
	second := awaitHead(t, heads)
	stopPurchases()
	closeMiner.Do(b.miner.Close)
	verifyMinedPurchase(t, verifier, first, hash, initial.NumberU64()+1)
	verifyMinedPurchase(t, verifier, second, automatic.tx.Hash(), initial.NumberU64()+2)
	t.Logf("canonical-head notification: next automatic purchase mined at height=%d; both independent imports passed after stopping the producer", second.NumberU64())
}

func startPurchaseController(t *testing.T, enabled bool) func() {
	t.Helper()
	buyer := ethapi.NewTicketBuyer(enabled)
	requireNoError(t, buyer.Start())
	var once sync.Once
	stop := func() {
		done := make(chan struct{})
		go func() {
			once.Do(func() { buyer.Stop() })
			close(done)
		}()
		select {
		case <-done:
		case <-time.After(10 * time.Second):
			t.Fatal("purchase controller did not stop")
		}
		common.SetAutoBuyTicketEnabled(false)
	}
	t.Cleanup(stop)
	return stop
}

func advancePurchaseFixture(t *testing.T, f, verifier *fixture) {
	t.Helper()
	jump := uint64(time.Now().Unix()) - 3600
	for i := 0; i < 14; i++ {
		timestamp := f.chain.CurrentBlock().Time() + 120
		if i == 2 {
			timestamp = jump
		}
		var txs []*types.Transaction
		if i > 0 {
			txs = append(txs, f.signPurchase(t, f.chain.CurrentBlock().Time(), common.TimeLockForever))
		}
		block := f.buildBlockWithTransactions(t, timestamp, txs)
		f.importBlock(t, block)
		if verifier != nil {
			verifier.importBlock(t, block)
		}
	}
}

func awaitSubmission(t *testing.T, b *autoBuyBackend) purchaseSubmission {
	t.Helper()
	select {
	case submission := <-b.submissions:
		return submission
	case <-time.After(10 * time.Second):
		t.Fatalf("purchase did not reach submission; builds=%d", b.buildCalls.Load())
		return purchaseSubmission{}
	}
}

func awaitHead(t *testing.T, heads <-chan core.ChainHeadEvent) *types.Block {
	t.Helper()
	select {
	case head := <-heads:
		return head.Block
	case <-time.After(25 * time.Second):
		t.Fatal("miner did not produce a successor")
		return nil
	}
}

func verifyMinedPurchase(t *testing.T, verifier *fixture, block *types.Block, hash common.Hash, height uint64) {
	t.Helper()
	if block.NumberU64() != height || len(block.Transactions()) != 1 || block.Transactions()[0].Hash() != hash {
		t.Fatal("mined block does not contain the expected replacement purchase")
	}
	verifier.importBlock(t, block)
	statedb, err := verifier.chain.State()
	requireNoError(t, err)
	parentHash := block.ParentHash()
	if !statedb.IsTicketExist(crypto.Keccak256Hash(verifier.owner[:], parentHash[:])) {
		t.Fatal("independent execution did not create the replacement ticket")
	}
}
