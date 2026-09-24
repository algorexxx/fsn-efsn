package restart

import (
	"os"
	"path/filepath"
	"strconv"
	"testing"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"golang.org/x/sys/unix"
)

func TestPreservedReplayHeadReadOnly(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_INSPECT_REPLAY_DIR")
	if directory == "" {
		t.Skip("set FUSION_RESTART_INSPECT_REPLAY_DIR and FUSION_RESTART_INSPECT_REPLAY_HEIGHT to check a closed replay")
	}
	backup := openInspectionBackup(t)
	expected, err := strconv.ParseUint(os.Getenv("FUSION_RESTART_INSPECT_REPLAY_HEIGHT"), 10, 64)
	requireNoError(t, err)
	if !filepath.IsAbs(directory) || expected == 0 || expected > backup.head.Number.Uint64() {
		t.Fatal("replay inspection requires an absolute target path and a preserved nonzero height")
	}
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(directory, &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("closed replay inspection requires a read-only mount")
	}
	verifyReplayHead(t, backup, directory, expected)
	db, err := rawdb.NewLevelDBDatabase(directory, 128, 64, "restart-closed-head", true)
	requireNoError(t, err)
	defer func() { requireNoError(t, db.Close()) }()
	hash := rawdb.ReadHeadBlockHash(db)
	if hash != rawdb.ReadCanonicalHash(backup.db, expected) {
		t.Fatal("closed replay head differs from the requested exact height")
	}
	header := rawdb.ReadHeader(db, hash, expected)
	if header == nil {
		t.Fatal("closed replay header is missing")
	}
	t.Logf("closed replay matched: height=%d hash=%s root=%s ticketCommitment=%s", expected, hash.Hex(), header.Root.Hex(), header.MixDigest.Hex())
}
