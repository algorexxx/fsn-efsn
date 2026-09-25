package restart

import (
	"bytes"
	"context"
	"errors"
	"os"
	"os/exec"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts/keystore"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
)

type purchaseStorageFault struct {
	ethdb.Database
	key       []byte
	operation string
	after     bool
	enabled   atomic.Bool
	attempts  chan []byte
}

func (d *purchaseStorageFault) fails(operation string, key []byte) bool {
	return d.enabled.Load() && d.operation == operation && bytes.Equal(key, d.key)
}

func (d *purchaseStorageFault) Put(key, value []byte) error {
	if !d.fails("put", key) {
		return d.Database.Put(key, value)
	}
	select {
	case d.attempts <- append([]byte(nil), value...):
	default:
	}
	if d.after {
		if err := d.Database.Put(key, value); err != nil {
			return err
		}
	}
	return errors.New("injected automatic record put failure")
}

func (d *purchaseStorageFault) Delete(key []byte) error {
	if !d.fails("delete", key) {
		return d.Database.Delete(key)
	}
	if d.after {
		if err := d.Database.Delete(key); err != nil {
			return err
		}
	}
	return errors.New("injected automatic record delete failure")
}

func (d *purchaseStorageFault) Has(key []byte) (bool, error) {
	if d.fails("has", key) {
		return false, errors.New("injected automatic record has failure")
	}
	return d.Database.Has(key)
}

func (d *purchaseStorageFault) Get(key []byte) ([]byte, error) {
	if d.fails("get", key) {
		return nil, errors.New("injected automatic record get failure")
	}
	return d.Database.Get(key)
}

func TestAutomaticPurchaseStorageErrors(t *testing.T) {
	if mode := os.Getenv("FUSION_PURCHASE_STORAGE_CHILD"); mode != "" {
		runPurchaseRecovery(t, mode)
		return
	}
	for _, mode := range []string{"put_before", "put_after", "adopt_before", "adopt_after", "delete_before", "delete_after", "has", "get"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestAutomaticPurchaseStorageErrors$", "-test.v", "-test.timeout=40s")
			command.Env = append(os.Environ(), "FUSION_PURCHASE_STORAGE_CHILD=storage_"+mode)
			output, err := command.CombinedOutput()
			t.Logf("storage fault %s:\n%s", mode, output)
			requireNoError(t, err)
		})
	}
}

func runPurchaseStorageError(t *testing.T, mode string, f *fixture, b *autoBuyBackend, keys *keystore.KeyStore, warnings <-chan string) {
	operation := strings.Split(strings.TrimPrefix(mode, "storage_"), "_")[0]
	adopt := operation == "adopt"
	var original *types.Transaction
	if adopt {
		original = f.signPurchase(t, f.chain.CurrentBlock().Time(), common.TimeLockForever)
		requireNoError(t, b.pool.AddLocal(original))
		operation = "put"
	} else if operation != "put" {
		b.failNext.Store(operation != "delete")
		stop := startPurchaseController(t, true)
		first := awaitSubmission(t, b)
		stop()
		original = first.tx
		if operation == "delete" {
			requireNoError(t, first.err)
			f.importBlock(t, f.buildBlockWithTransactions(t, f.chain.CurrentBlock().Time()+120, []*types.Transaction{original}))
			awaitPoolNonce(t, b, original.Nonce()+1)
		} else {
			requireErrorContains(t, first.err, "injected temporary submission failure")
			awaitPurchaseWarning(t, warnings, "injected temporary submission failure")
		}
	}
	head := f.chain.CurrentBlock()
	state, err := f.chain.State()
	requireNoError(t, err)
	nonce := state.GetNonce(f.owner)
	fault := &purchaseStorageFault{Database: f.db, key: append([]byte("fsn-auto-ticket-v1-"), f.owner[:]...), operation: operation, after: strings.HasSuffix(mode, "_after"), attempts: make(chan []byte, 1)}
	fault.enabled.Store(true)
	b.database = fault
	confirmed := capturePurchaseLog(t, "Automatic ticket purchase confirmed")
	stop := startPurchaseController(t, true)
	awaitPurchaseWarning(t, warnings, "injected automatic record "+operation+" failure")
	stop()
	select {
	case result := <-b.submissions:
		t.Fatalf("storage failure submitted transaction %s: %v", result.tx.Hash(), result.err)
	default:
	}
	saved := readAutomaticPurchaseRecord(t, f.db, f.owner)
	var attempted []byte
	if operation == "put" {
		attempted = <-fault.attempts
		if fault.after {
			requirePurchaseStorageBytes(t, saved, attempted)
		} else if saved != nil {
			t.Fatal("failed pre-write save created a record")
		}
	} else if operation == "delete" && fault.after {
		if saved != nil {
			t.Fatal("post-delete error retained a record")
		}
	} else {
		encoded, err := original.MarshalBinary()
		requireNoError(t, err)
		requirePurchaseStorageBytes(t, saved, encoded)
	}
	if !fault.after {
		stop = startPurchaseController(t, true)
		assertPurchaseQuiet(t, b)
		stop()
	}
	if adopt || operation == "has" || operation == "get" || (operation == "put" && fault.after) {
		requireNoError(t, keys.Lock(f.owner))
	}
	fault.enabled.Store(false)
	stop = startPurchaseController(t, true)
	var recovered *types.Transaction
	if adopt {
		deadline := time.After(10 * time.Second)
		for recovered == nil {
			recovered = readAutomaticPurchaseRecord(t, f.db, f.owner)
			select {
			case <-deadline:
				t.Fatal("pool purchase was not adopted after storage recovered")
			default:
				time.Sleep(10 * time.Millisecond)
			}
		}
	} else {
		result := awaitSubmission(t, b)
		requireNoError(t, result.err)
		recovered = result.tx
	}
	assertPurchaseQuiet(t, b)
	stop()
	encoded, err := recovered.MarshalBinary()
	requireNoError(t, err)
	requirePurchaseStorageBytes(t, readAutomaticPurchaseRecord(t, f.db, f.owner), encoded)
	if recovered.Nonce() != nonce || b.pool.Get(recovered.Hash()) == nil {
		t.Fatal("recovered purchase does not match canonical nonce and pool")
	}
	if adopt || operation == "has" || operation == "get" {
		if recovered.Hash() != original.Hash() {
			t.Fatal("recovery replaced the original signed purchase")
		}
	} else if operation == "put" && fault.after && !bytes.Equal(encoded, attempted) {
		t.Fatal("recovery replaced the purchase saved before the error")
	}
	wantConfirmations := 0
	if operation == "delete" && !fault.after {
		wantConfirmations = 1
	}
	if len(confirmed) != wantConfirmations {
		t.Fatalf("confirmation count %d, expected %d", len(confirmed), wantConfirmations)
	}
	pending, queued := b.pool.Stats()
	if pending+queued != 1 || f.chain.CurrentBlock().Hash() != head.Hash() {
		t.Fatal("storage recovery changed head or produced extra pool entries")
	}
	t.Logf("%s: failure paused submission; recovery retained one purchase at canonical nonce %d, hash %s; confirmations=%d", mode, nonce, recovered.Hash().Hex(), len(confirmed))
}

func requirePurchaseStorageBytes(t *testing.T, tx *types.Transaction, expected []byte) {
	t.Helper()
	if tx == nil {
		t.Fatal("expected automatic purchase record")
	}
	encoded, err := tx.MarshalBinary()
	requireNoError(t, err)
	if !bytes.Equal(encoded, expected) {
		t.Fatal("automatic purchase bytes changed")
	}
}
