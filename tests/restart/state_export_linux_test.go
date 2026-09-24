package restart

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"golang.org/x/sys/unix"
)

func TestPreservedStateExport(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_STATE_EXPORT_DIR")
	if directory == "" {
		t.Skip("set FUSION_RESTART_STATE_EXPORT_DIR to an absolute new directory for state-only extraction")
	}
	backup := openInspectionBackup(t)
	var sourceMount unix.Statfs_t
	requireNoError(t, unix.Statfs(os.Getenv("FUSION_RESTART_CHAINDATA"), &sourceMount))
	if sourceMount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("state export requires a read-only source mount")
	}
	requireReplaySpace(t, filepath.Dir(directory))
	identity := stateExportIdentity{
		Format: 1, Genesis: rawdb.ReadCanonicalHash(backup.db, 0),
		Head: &backup.head, Config: backup.config, ExecutableHash: stateExportExecutableHash(t),
	}
	requireNoError(t, createStateExportDirectory(directory, identity))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 256, 128, "restart-state-export", false)
	requireNoError(t, err)
	closed := false
	t.Cleanup(func() {
		if !closed {
			requireNoError(t, db.Close())
		}
	})
	lastProgress := time.Now()
	result, err := exportState(backup.db, db, backup.head.Root, func(current stateExportProgress) error {
		requireReplaySpace(t, directory)
		if stop := os.Getenv("FUSION_RESTART_STATE_EXPORT_STOP_FILE"); stop != "" {
			if _, err := os.Stat(stop); err == nil {
				t.Fatal("state export stopped by stop file; artifact remains unverified")
			} else if !os.IsNotExist(err) {
				return err
			}
		}
		if time.Since(lastProgress) >= 20*time.Second {
			t.Logf("state export progress: %+v", current)
			lastProgress = time.Now()
		}
		return nil
	})
	t.Logf("state export result: %+v root=%s error=%v", result, backup.head.Root.Hex(), err)
	requireNoError(t, err)
	requireNoError(t, db.Close())
	closed = true
	t.Logf("closed state-only export: %s; cold verification required", directory)
}
