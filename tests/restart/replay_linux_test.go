package restart

import (
	"math/big"
	"os"
	"path/filepath"
	"strconv"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"golang.org/x/sys/unix"
)

func TestPreservedHistoryReplay(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_REPLAY_DIR")
	if directory == "" {
		t.Skip("set an explicit new FUSION_RESTART_REPLAY_DIR and FUSION_RESTART_REPLAY_END for isolated replay")
	}
	backup := openInspectionBackup(t)
	end, err := strconv.ParseUint(os.Getenv("FUSION_RESTART_REPLAY_END"), 10, 64)
	requireNoError(t, err)
	if end == 0 || end > backup.head.Number.Uint64() {
		t.Fatal("replay end must be within the preserved history")
	}
	if !filepath.IsAbs(directory) {
		t.Fatal("replay directory must be an absolute path")
	}
	if _, err := os.Stat(directory); !os.IsNotExist(err) {
		t.Fatal("replay requires a new, nonexistent directory; existing databases are never overwritten")
	}
	requireReplaySpace(t, filepath.Dir(directory))
	requireNoError(t, os.Mkdir(directory, 0700))
	db, err := rawdb.NewLevelDBDatabase(directory, 256, 128, "restart-replay", false)
	requireNoError(t, err)
	t.Cleanup(func() { requireNoError(t, db.Close()) })
	genesis := core.DefaultGenesisBlock()
	block, err := genesis.Commit(db)
	requireNoError(t, err)
	if block.Hash() != rawdb.ReadCanonicalHash(backup.db, 0) {
		t.Fatal("generated mainnet genesis differs from preserved genesis")
	}
	datong.InitCheckPoints("")
	t.Logf("baseline replay: end=%d legacyCheckpointRangeEnd=%d; ticket-seal and raw-transaction shortcuts remain active in that historical range", end, datong.LastCheckPoint)
	cache := &core.CacheConfig{TrieCleanLimit: 128, TrieDirtyLimit: 256, TrieTimeLimit: 5 * time.Minute}
	engine := datong.New(genesis.Config.DaTong, db)
	chain, err := core.NewBlockChain(db, cache, genesis.Config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	t.Cleanup(chain.Stop)
	lastProgress := time.Now()
	for first := uint64(1); first <= end; {
		requireReplaySpace(t, directory)
		last := first + 127
		if last > end {
			last = end
		}
		blocks := make(types.Blocks, 0, last-first+1)
		for number := first; number <= last; number++ {
			hash := rawdb.ReadCanonicalHash(backup.db, number)
			block := rawdb.ReadBlock(backup.db, hash, number)
			if block == nil || block.Hash() != hash || block.NumberU64() != number {
				t.Fatalf("missing or inconsistent source block %d", number)
			}
			blocks = append(blocks, block)
		}
		failedIndex, err := chain.InsertChain(blocks)
		if err != nil {
			t.Fatalf("replay failed at batch starting %d, index %d: %v", first, failedIndex, err)
		}
		if chain.CurrentBlock().Hash() != blocks[len(blocks)-1].Hash() {
			t.Fatalf("replay did not advance to expected height %d", last)
		}
		if time.Since(lastProgress) >= 20*time.Second {
			t.Logf("replay progress: height=%d root=%s", last, chain.CurrentBlock().Root().Hex())
			lastProgress = time.Now()
		}
		first = last + 1
	}
	final := chain.CurrentBlock()
	if final.Number().Cmp(new(big.Int).SetUint64(end)) != 0 {
		t.Fatal("replay ended at the wrong height")
	}
	statedb, err := chain.State()
	requireNoError(t, err)
	tickets, err := statedb.AllTickets()
	requireNoError(t, err)
	requireNoError(t, state.AddCachedTickets(final.MixDigest(), tickets))
	t.Logf("replay matched: height=%d hash=%s root=%s ticketCommitment=%s tickets=%d", end, final.Hash().Hex(), final.Root().Hex(), final.MixDigest().Hex(), tickets.NumberOfTickets())
}

func requireReplaySpace(t *testing.T, directory string) {
	t.Helper()
	host := os.Getenv("FUSION_RESTART_HOST_STORAGE")
	if host == "" {
		t.Fatal("FUSION_RESTART_HOST_STORAGE must name the Windows host drive mount")
	}
	for path, reserve := range map[string]uint64{directory: 20 * 1024 * 1024 * 1024, host: 50 * 1024 * 1024 * 1024} {
		var capacity unix.Statfs_t
		requireNoError(t, unix.Statfs(path, &capacity))
		available := capacity.Bavail * uint64(capacity.Bsize)
		if available < reserve {
			t.Fatalf("replay stopped before next batch: %s has %d bytes free, reserve %d", path, available, reserve)
		}
	}
}
