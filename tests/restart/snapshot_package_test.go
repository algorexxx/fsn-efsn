package restart

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
)

func TestSnapshotReadOnlySourceLock(t *testing.T) {
	path := filepath.Join(t.TempDir(), "chaindata")
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "snapshot-lock-test", false)
	requireNoError(t, err)
	requireNoError(t, db.Put([]byte("preserved"), []byte("original")))
	requireNoError(t, db.Close())
	reader, err := rawdb.NewLevelDBDatabase(path, 16, 16, "snapshot-lock-test", true)
	requireNoError(t, err)
	defer reader.Close()
	writer, err := rawdb.NewLevelDBDatabase(path, 16, 16, "snapshot-lock-test", false)
	if err == nil {
		writer.Close()
		t.Fatal("writable open succeeded while source held read-only")
	}
	t.Logf("concurrent writable source open refused: %v", err)
	value, err := reader.Get([]byte("preserved"))
	requireNoError(t, err)
	if string(value) != "original" {
		t.Fatal("source value changed")
	}
}

func TestPreservedSnapshotPackage(t *testing.T) {
	target := os.Getenv("FUSION_RESTART_PACKAGE")
	if target == "" {
		t.Skip("requires explicit stopped preserved source and new package directory")
	}
	if !filepath.IsAbs(target) {
		t.Fatal("absolute package path required")
	}
	backup := openInspectionBackup(t)
	reader, err := recovery.NewReader(backup.db)
	requireNoError(t, err)
	head := reader.CurrentHeader()
	if head.Hash() != backup.head.Hash() {
		t.Fatal("head markers disagree")
	}
	identity, err := json.MarshalIndent(map[string]interface{}{"genesis": rawdb.ReadCanonicalHash(backup.db, 0), "head": head, "chain_config": backup.config}, "", "  ")
	requireNoError(t, err)
	identityPath := filepath.Join(t.TempDir(), "identity.json")
	requireNoError(t, os.WriteFile(identityPath, identity, 0600))
	arguments := []string{"-3", "snapshot_package.py", "pack", "--source", os.Getenv("FUSION_RESTART_CHAINDATA"), "--destination", target, "--identity", identityPath, "--stop", filepath.Join(filepath.Dir(target), "STOP-PACKAGE")}
	if os.Getenv("FUSION_RESTART_PACKAGE_RESUME") == "1" {
		arguments = append(arguments, "--resume")
	}
	if maximum := os.Getenv("FUSION_RESTART_PACKAGE_MAX_PARTS"); maximum != "" {
		arguments = append(arguments, "--max-parts", maximum)
	}
	command := exec.Command("py", arguments...)
	command.Stdout, command.Stderr = os.Stdout, os.Stderr
	requireNoError(t, command.Run())
	if rawdb.ReadHeadBlockHash(backup.db) != backup.head.Hash() {
		t.Fatal("source head changed")
	}
	t.Log("package attempt finished with source held open read-only; only a checksummed final manifest denotes a complete package")
}
