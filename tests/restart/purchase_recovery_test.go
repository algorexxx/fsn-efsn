package restart

import (
	"context"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/accounts/keystore"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/log"
)

func TestAutomaticPurchaseRecovery(t *testing.T) {
	if mode := os.Getenv("FUSION_PURCHASE_RECOVERY_CHILD"); mode != "" {
		runPurchaseRecovery(t, mode)
		return
	}
	for _, mode := range []string{"gates", "wallet", "estimate", "funding", "restart_failed", "restart_journal", "replacement_reorg", "later_ticket", "corrupt_saved"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestAutomaticPurchaseRecovery$", "-test.v", "-test.timeout=55s")
			command.Env = append(os.Environ(), "FUSION_PURCHASE_RECOVERY_CHILD="+mode)
			output, err := command.CombinedOutput()
			t.Logf("isolated recovery %s:\n%s", mode, output)
			requireNoError(t, err)
		})
	}
}

func runPurchaseRecovery(t *testing.T, mode string) {
	path := filepath.Join(t.TempDir(), "chaindata")
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "restart-test", false)
	requireNoError(t, err)
	f := newFixtureInDatabase(t, common.TimeLockForever, db)
	advancePurchaseFixture(t, f, nil)
	initial := f.chain.CurrentBlock()
	keys := keystore.NewKeyStore(t.TempDir(), keystore.LightScryptN, keystore.LightScryptP)
	account, err := keys.ImportECDSA(f.key, "synthetic-test-key")
	requireNoError(t, err)
	requireNoError(t, keys.Unlock(account, "synthetic-test-key"))
	manager := accounts.NewManager(keys)
	t.Cleanup(func() { manager.Close() })
	config := core.DefaultTxPoolConfig
	config.Journal = filepath.Join(t.TempDir(), "transactions.rlp")
	b := &autoBuyBackend{purchaseBackend: &purchaseBackend{chain: f.chain}, pool: core.NewTxPool(config, f.chain.Config(), f.chain), accounts: manager, owner: f.owner, database: f.db, submissions: make(chan purchaseSubmission, 16)}
	t.Cleanup(func() { b.pool.Stop() })
	b.mining.Store(true)
	lock := new(ethapi.AddrLocker)
	ethapi.NewFusionTransactionAPI(b, lock, ethapi.NewPublicTransactionPoolAPI(b, lock))
	warnings := capturePurchaseLog(t, "Automatic ticket purchase needs attention; retrying")
	switch mode {
	case "gates":
		b.mining.Store(false)
		stop := startPurchaseController(t, false)
		assertPurchaseQuiet(t, b)
		common.SetAutoBuyTicketEnabled(true)
		assertPurchaseQuiet(t, b)
		if b.buildCalls.Load() != 0 {
			t.Fatal("disabled mining reached purchase construction")
		}
		b.mining.Store(true)
		requireNoError(t, awaitSubmission(t, b).err)
		stop()
		assertPurchaseQuiet(t, b)
		t.Log("disabled auto-buy, disabled mining, startup, and cancellation respected without a head change")
	case "wallet", "estimate", "funding":
		expected := "authentication needed"
		if mode == "wallet" {
			requireNoError(t, keys.Lock(account.Address))
		} else if mode == "estimate" {
			b.failEstimate.Store(true)
			expected = "injected gas estimation failure"
		} else {
			b.noFunds.Store(true)
			expected = "not enough time lock or asset balance"
		}
		stop := startPurchaseController(t, true)
		awaitPurchaseWarning(t, warnings, expected)
		requireNoError(t, keys.Unlock(account, "synthetic-test-key"))
		b.failEstimate.Store(false)
		b.noFunds.Store(false)
		requireNoError(t, awaitSubmission(t, b).err)
		stop()
		t.Logf("%s failure recovered automatically without a head change", mode)
	case "restart_failed", "restart_journal":
		b.failNext.Store(mode == "restart_failed")
		stop := startPurchaseController(t, true)
		first := awaitSubmission(t, b)
		if mode == "restart_failed" {
			requireErrorContains(t, first.err, "injected temporary submission failure")
		} else {
			requireNoError(t, first.err)
		}
		stop()
		b.pool.Stop()
		f.chain.Stop()
		requireNoError(t, f.db.Close())
		f.db, err = rawdb.NewLevelDBDatabase(path, 16, 16, "restart-test", false)
		requireNoError(t, err)
		f.engine = datong.New(f.chain.Config().DaTong, f.db)
		f.chain, err = core.NewBlockChain(f.db, &core.CacheConfig{TrieDirtyDisabled: true}, f.chain.Config(), f.engine, vm.Config{}, nil)
		requireNoError(t, err)
		b.chain, b.database = f.chain, f.db
		b.pool = core.NewTxPool(config, f.chain.Config(), f.chain)
		requireNoError(t, keys.Lock(account.Address))
		stop = startPurchaseController(t, true)
		if mode == "restart_failed" {
			retried := awaitSubmission(t, b)
			requireNoError(t, retried.err)
			if retried.tx.Hash() != first.tx.Hash() {
				t.Fatal("restart changed the saved signed transaction")
			}
		} else {
			if b.pool.Get(first.tx.Hash()) == nil {
				t.Fatal("local pool journal did not restore the purchase")
			}
			assertPurchaseQuiet(t, b)
		}
		stop()
		t.Logf("%s: reopened LevelDB and pool with locked wallet; exact saved transaction retained", mode)
	case "replacement_reorg":
		runPurchaseReplacementReorg(t, f, b, keys, warnings)
		return
	case "later_ticket":
		stop := startPurchaseController(t, true)
		first := awaitSubmission(t, b)
		requireNoError(t, first.err)
		stop()
		later, err := types.SignTx(types.NewTransaction(first.tx.Nonce()+1, *first.tx.To(), first.tx.Value(), first.tx.Gas(), first.tx.GasPrice(), first.tx.Data()), types.LatestSigner(f.chain.Config()), f.key)
		requireNoError(t, err)
		requireNoError(t, b.pool.AddLocal(later))
		if b.pool.Get(first.tx.Hash()) != nil {
			t.Fatal("pool did not evict the earlier purchase")
		}
		stop = startPurchaseController(t, true)
		awaitPurchaseWarning(t, warnings, "another ticket purchase")
		assertPurchaseQuiet(t, b)
		stop()
		if b.pool.Get(later.Hash()) == nil {
			t.Fatal("automatic retry removed the later-nonce ticket")
		}
		t.Log("later-nonce ticket was preserved despite the pool's one-ticket-per-owner rule")
	case "corrupt_saved":
		requireNoError(t, b.database.Put(append([]byte("fsn-auto-ticket-v1-"), f.owner[:]...), []byte("broken")))
		stop := startPurchaseController(t, true)
		awaitPurchaseWarning(t, warnings, "invalid saved automatic ticket")
		assertPurchaseQuiet(t, b)
		stop()
		t.Log("corrupt saved transaction stopped new automatic signing")
	default:
		t.Fatalf("unknown recovery mode %q", mode)
	}
	if f.chain.CurrentBlock().Hash() != initial.Hash() {
		t.Fatal("recovery scenario unexpectedly advanced the chain")
	}
}

func capturePurchaseLog(t *testing.T, message string) <-chan string {
	t.Helper()
	warnings := make(chan string, 32)
	previous := log.Root().GetHandler()
	log.Root().SetHandler(log.FuncHandler(func(record *log.Record) error {
		if record.Msg == message {
			select {
			case warnings <- fmt.Sprint(record.Ctx):
			default:
			}
		}
		return previous.Log(record)
	}))
	t.Cleanup(func() { log.Root().SetHandler(previous) })
	return warnings
}

func awaitPurchaseWarning(t *testing.T, warnings <-chan string, expected string) {
	t.Helper()
	select {
	case warning := <-warnings:
		if !strings.Contains(warning, expected) {
			t.Fatalf("expected warning %q, got %q", expected, warning)
		}
	case <-time.After(10 * time.Second):
		t.Fatalf("missing warning %q", expected)
	}
}

func assertPurchaseQuiet(t *testing.T, b *autoBuyBackend) {
	t.Helper()
	select {
	case submitted := <-b.submissions:
		t.Fatalf("unexpected purchase submission: %s (%v)", submitted.tx.Hash(), submitted.err)
	case <-time.After(6 * time.Second):
	}
}

func runPurchaseReplacementReorg(t *testing.T, f *fixture, b *autoBuyBackend, keys *keystore.KeyStore, warnings <-chan string) {
	initial := f.chain.CurrentBlock()
	stop := startPurchaseController(t, true)
	first := awaitSubmission(t, b)
	requireNoError(t, first.err)
	stop()
	price := new(big.Int).Mul(first.tx.GasPrice(), big.NewInt(2))
	replacement, err := types.SignTx(types.NewTransaction(first.tx.Nonce(), f.owner, big.NewInt(0), 21000, price, nil), types.LatestSigner(f.chain.Config()), f.key)
	requireNoError(t, err)
	requireNoError(t, b.pool.AddLocal(replacement))
	stop = startPurchaseController(t, true)
	awaitPurchaseWarning(t, warnings, "was replaced at nonce")
	assertPurchaseQuiet(t, b)
	stop()
	block := f.buildBlockWithTransactions(t, initial.Time()+120, []*types.Transaction{replacement})
	f.importBlock(t, block)
	awaitPoolNonce(t, b, replacement.Nonce()+1)
	stop = startPurchaseController(t, true)
	second := awaitSubmission(t, b)
	requireNoError(t, second.err)
	stop()
	if second.tx.Nonce() != first.tx.Nonce()+1 {
		t.Fatal("controller did not follow the canonically consumed nonce")
	}
	b.pool.Stop()
	requireNoError(t, f.chain.SetHead(initial.NumberU64()))
	config := core.DefaultTxPoolConfig
	config.Journal = ""
	b.pool = core.NewTxPool(config, f.chain.Config(), f.chain)
	requireNoError(t, keys.Lock(f.owner))
	stop = startPurchaseController(t, true)
	awaitPurchaseWarning(t, warnings, fmt.Sprintf("needs nonce %d, current nonce is %d", second.tx.Nonce(), first.tx.Nonce()))
	assertPurchaseQuiet(t, b)
	stop()
	alternative := f.buildBlockWithTransactions(t, initial.Time()+121, []*types.Transaction{first.tx})
	f.importBlock(t, alternative)
	if alternative.NumberU64() != block.NumberU64() || alternative.Hash() == block.Hash() {
		t.Fatal("fixture did not replace the head at the same height")
	}
	awaitPoolNonce(t, b, second.tx.Nonce())
	stop = startPurchaseController(t, true)
	retried := awaitSubmission(t, b)
	requireNoError(t, retried.err)
	stop()
	if retried.tx.Hash() != second.tx.Hash() {
		t.Fatal("changed head or lost pool caused a different transaction to be signed")
	}
	f.importBlock(t, f.buildBlockWithTransactions(t, alternative.Time()+120, []*types.Transaction{retried.tx}))
	t.Log("automatic buying paused for a conflicting transfer and a rewind nonce gap, resumed after inclusion, and recovered the exact next purchase after a same-height canonical replacement and pool loss")
}

func awaitPoolNonce(t *testing.T, b *autoBuyBackend, nonce uint64) {
	t.Helper()
	timeout := time.After(5 * time.Second)
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()
	for b.pool.Nonce(b.owner) != nonce {
		select {
		case <-timeout:
			t.Fatal("pool did not process the new canonical nonce")
		case <-ticker.C:
		}
	}
}
