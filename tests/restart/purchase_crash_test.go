package restart

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/log"
)

type purchaseCrashBoundary struct {
	directory string
	cut       string
	phase     string
	armed     bool
}

func (b *purchaseCrashBoundary) hit(cut, phase string) {
	if b.armed && b.cut == cut && b.phase == phase {
		fmt.Printf("PURCHASE-CRASH %s %s\n", cut, phase)
		os.Exit(86)
	}
}

type purchaseCrashDatabase struct {
	ethdb.Database
	boundary *purchaseCrashBoundary
	key      []byte
}

func (db *purchaseCrashDatabase) Put(key, value []byte) error {
	if !db.boundary.armed || !bytes.Equal(key, db.key) {
		return db.Database.Put(key, value)
	}
	if err := os.WriteFile(filepath.Join(db.boundary.directory, "attempt.bin"), value, 0600); err != nil {
		return err
	}
	db.boundary.hit("save", "before")
	err := db.Database.Put(key, value)
	if err == nil {
		db.boundary.hit("save", "after")
	}
	return err
}

func (db *purchaseCrashDatabase) Delete(key []byte) error {
	if !db.boundary.armed || !bytes.Equal(key, db.key) {
		return db.Database.Delete(key)
	}
	db.boundary.hit("retire", "before")
	err := db.Database.Delete(key)
	if err == nil {
		db.boundary.hit("retire", "after")
	}
	return err
}

type purchaseCrashBackend struct {
	*autoBuyBackend
	boundary *purchaseCrashBoundary
}

func (b *purchaseCrashBackend) SendTx(ctx context.Context, tx *types.Transaction) error {
	b.boundary.hit("submit", "before")
	err := b.autoBuyBackend.SendTx(ctx, tx)
	if err == nil {
		b.boundary.hit("submit", "after")
	}
	return err
}

func TestAutomaticPurchaseCrashBoundaries(t *testing.T) {
	if os.Getenv("FUSION_PURCHASE_CRASH_REHEARSAL") != "1" {
		t.Skip("opt-in abrupt purchase restart checks use disposable sparse databases")
	}
	if action := os.Getenv("FUSION_PURCHASE_CRASH_ACTION"); action != "" {
		log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
		runPurchaseCrashAction(t, action)
		return
	}
	for _, scenario := range []string{"new", "confirmed", "replaced", "adopt"} {
		cuts := []string{"save"}
		if scenario == "new" {
			cuts = append(cuts, "submit")
		} else if scenario == "confirmed" {
			cuts = append(cuts, "retire")
		} else if scenario == "replaced" {
			cuts = []string{"retire"}
		}
		pools := []string{"restore"}
		if scenario == "new" {
			pools = append(pools, "lost")
		}
		for _, pool := range pools {
			for _, cut := range cuts {
				for _, phase := range []string{"before", "after"} {
					t.Run(scenario+"/"+pool+"/"+cut+"/"+phase, func(t *testing.T) {
						directory := t.TempDir()
						for _, action := range []string{"prepare", "crash", "recover", "cold"} {
							runPurchaseCrashChild(t, directory, scenario, pool, cut, phase, action)
						}
						t.Log("abrupt cut reached; exact surviving purchase or correct unconsumed nonce recovered; cold record/pool agree")
					})
				}
			}
		}
	}
}

func runPurchaseCrashChild(t *testing.T, directory, scenario, pool, cut, phase, action string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestAutomaticPurchaseCrashBoundaries$", "-test.v", "-test.timeout=40s")
	command.Env = append(os.Environ(), "FUSION_PURCHASE_CRASH_ACTION="+action, "FUSION_PURCHASE_CRASH_DIR="+directory, "FUSION_PURCHASE_CRASH_SCENARIO="+scenario, "FUSION_PURCHASE_CRASH_POOL="+pool, "FUSION_PURCHASE_CRASH_CUT="+cut, "FUSION_PURCHASE_CRASH_PHASE="+phase)
	output, err := command.CombinedOutput()
	if bytes.Contains(output, []byte("WARNING: DATA RACE")) {
		t.Fatalf("purchase crash child reported a race:\n%s", output)
	}
	if action == "crash" {
		var failure *exec.ExitError
		if !errors.As(err, &failure) || failure.ExitCode() != 86 || !bytes.Contains(output, []byte("PURCHASE-CRASH "+cut+" "+phase)) {
			t.Fatalf("requested abrupt cut not reached: %v\n%s", err, output)
		}
		return
	}
	if err != nil || !bytes.Contains(output, []byte("PASS")) {
		t.Fatalf("purchase %s failed: %v\n%s", action, err, output)
	}
	if action == "recover" {
		t.Logf("recovery observations:\n%s", output)
	}
}

func runPurchaseCrashAction(t *testing.T, action string) {
	directory, scenario := os.Getenv("FUSION_PURCHASE_CRASH_DIR"), os.Getenv("FUSION_PURCHASE_CRASH_SCENARIO")
	if !filepath.IsAbs(directory) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("disposable absolute path and no backup environment required")
	}
	if action == "prepare" {
		db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 16, 16, "purchase-crash", false)
		requireNoError(t, err)
		f := newFixtureInDatabase(t, common.TimeLockForever, db)
		advancePurchaseFixture(t, f, nil)
		return
	}
	f, keys, backend := openPurchaseCrashFixture(t, directory)
	if action == "cold" {
		verifyPurchaseCrashCold(t, directory, f, backend)
		return
	}
	if action == "recover" {
		recoverPurchaseCrash(t, directory, scenario, f, keys, backend)
		return
	}
	if action != "crash" {
		t.Fatal("unknown child action")
	}
	requireNoError(t, keys.Unlock(keys.Accounts()[0], "public crash key"))
	preparePurchaseCrashScenario(t, directory, scenario, f, backend.autoBuyBackend)
	requireNoError(t, writeStateExportJSON(filepath.Join(directory, "head.json"), f.chain.CurrentBlock().Header()))
	backend.boundary.cut = os.Getenv("FUSION_PURCHASE_CRASH_CUT")
	backend.boundary.phase = os.Getenv("FUSION_PURCHASE_CRASH_PHASE")
	backend.boundary.armed = true
	startPurchaseController(t, true)
	select {
	case <-time.After(15 * time.Second):
		t.Fatal("controller did not reach requested cut")
	}
}
