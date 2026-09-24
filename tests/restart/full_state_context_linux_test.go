package restart

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"golang.org/x/sys/unix"
)

func TestExportFullStateContext(t *testing.T) {
	path := os.Getenv("FUSION_RESTART_CONTEXT_OUTPUT")
	if path == "" {
		t.Skip("set FUSION_RESTART_CONTEXT_OUTPUT for read-only historical context extraction")
	}
	if !filepath.IsAbs(path) {
		t.Fatal("context output must be absolute and new")
	}
	backup := openInspectionBackup(t)
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(os.Getenv("FUSION_RESTART_CHAINDATA"), &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("context extraction requires a read-only source mount")
	}
	context := fullStateContext{Parent: rawdb.ReadBlock(backup.db, backup.head.Hash(), backup.head.Number.Uint64()), TotalDifficulty: rawdb.ReadTd(backup.db, backup.head.Hash(), backup.head.Number.Uint64()), Receipts: rawdb.ReadReceipts(backup.db, backup.head.Hash(), backup.head.Number.Uint64(), backup.config)}
	for height := backup.head.Number.Uint64() - 255; height <= backup.head.Number.Uint64(); height++ {
		context.Headers = append(context.Headers, rawdb.ReadHeader(backup.db, rawdb.ReadCanonicalHash(backup.db, height), height))
	}
	requireNoError(t, validateFullStateContext(&context, backup.head.Hash()))
	encoded, err := rlp.EncodeToBytes(&context)
	requireNoError(t, err)
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	_, err = file.Write(encoded)
	requireNoError(t, err)
	requireNoError(t, file.Close())
	t.Logf("verified context: first=%d last=%d headers=%d bytes=%d parent=%s TD=%s executable=%s", context.Headers[0].Number.Uint64(), backup.head.Number.Uint64(), len(context.Headers), len(encoded), backup.head.Hash().Hex(), context.TotalDifficulty, stateExportExecutableHash(t))
}
