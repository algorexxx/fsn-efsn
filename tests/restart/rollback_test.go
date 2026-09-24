package restart

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/log"
)

func TestRestartRollbackDatabaseModes(t *testing.T) {
	if mode := os.Getenv("FUSION_ROLLBACK_DATABASE_CHILD"); mode != "" {
		log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
		db := rawdb.NewMemoryDatabase()
		if mode == "leveldb" {
			var err error
			db, err = rawdb.NewLevelDBDatabase(t.TempDir(), 16, 16, "restart-rollback", false)
			requireNoError(t, err)
		}
		if mode == "storage_error" {
			db = &failingAncientDatabase{Database: db}
		}
		f := newFixtureInDatabase(t, 0, db)
		if mode == "storage_error" {
			f.chain.Rollback(nil)
			t.Fatal("real storage failure was ignored")
		}
		advancePurchaseFixture(t, f, newFixture(t))
		head := f.chain.CurrentBlock()
		parent := f.chain.GetBlock(head.ParentHash(), head.NumberU64()-1)
		f.chain.Rollback([]common.Hash{head.Hash()})
		requireCanonicalTip(t, f, parent)
		if f.chain.CurrentHeader().Hash() != parent.Hash() || f.chain.CurrentFastBlock().Hash() != parent.Hash() {
			t.Fatal("rollback left inconsistent memory heads")
		}
		if rawdb.ReadHeadHeaderHash(db) != parent.Hash() || rawdb.ReadHeadFastBlockHash(db) != parent.Hash() {
			t.Fatal("rollback left inconsistent persisted heads")
		}
		return
	}
	for _, mode := range []string{"memory", "leveldb", "storage_error"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartRollbackDatabaseModes$", "-test.v", "-test.timeout=25s")
			command.Env = append(os.Environ(), "FUSION_ROLLBACK_DATABASE_CHILD="+mode)
			output, err := command.CombinedOutput()
			t.Logf("rollback database %s:\n%s", mode, output)
			if mode == "storage_error" {
				var exit *exec.ExitError
				if !errors.As(err, &exit) || exit.ExitCode() != 1 || !strings.Contains(string(output), "CRIT") || !strings.Contains(string(output), "injected ancient storage read failure") {
					t.Fatalf("expected fatal storage error, got %v: %s", err, output)
				}
				return
			}
			requireNoError(t, err)
		})
	}
}

type failingAncientDatabase struct{ ethdb.Database }

func (db *failingAncientDatabase) Ancients() (uint64, error) {
	return 0, errors.New("injected ancient storage read failure")
}
