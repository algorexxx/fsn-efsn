package restart

import (
	"os"
	"strconv"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestT1FinalReplay(t *testing.T) {
	sourceDir, targetDir := os.Getenv("T1_SOURCE"), os.Getenv("T1_TARGET")
	if sourceDir == "" || targetDir == "" {
		t.Skip("T1_SOURCE and T1_TARGET required")
	}
	end, err := strconv.ParseUint(os.Getenv("T1_END"), 10, 64)
	requireNoError(t, err)
	source, err := rawdb.NewLevelDBDatabase(sourceDir, 128, 64, "t1-source", true)
	requireNoError(t, err)
	defer source.Close()
	target, err := rawdb.NewLevelDBDatabase(targetDir, 512, 256, "t1-target", false)
	requireNoError(t, err)
	defer target.Close()
	if rawdb.ReadCanonicalHash(source, 0) != params.MainnetGenesisHash || rawdb.ReadCanonicalHash(target, 0) != params.MainnetGenesisHash {
		t.Fatal("source or target is not mainnet")
	}
	if rawdb.ReadCanonicalHash(source, end) == (common.Hash{}) {
		t.Fatal("end is beyond the source history")
	}
	datong.InitCheckPoints("")
	genesis := core.DefaultGenesisBlock()
	engine := datong.New(genesis.Config.DaTong, target)
	startHead := rawdb.ReadHeadBlockHash(target)
	chain, err := core.NewBlockChain(target, &core.CacheConfig{TrieCleanLimit: 256, TrieDirtyLimit: 512, TrieTimeLimit: 5 * time.Minute}, genesis.Config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	start := chain.CurrentBlock()
	if start.Hash() != startHead || rawdb.ReadCanonicalHash(source, start.NumberU64()) != start.Hash() {
		t.Fatalf("start head %d %s is not the stored head or not canonical in the source", start.NumberU64(), start.Hash().Hex())
	}
	t.Logf("T1 replay start=%d hash=%s end=%d lastCheckPoint=%d pins=%d", start.NumberU64(), start.Hash().Hex(), end, datong.LastCheckPoint, len(datong.CheckPoints))
	began, lastLog := time.Now(), time.Now()
	for first := start.NumberU64() + 1; first <= end; {
		if stop := os.Getenv("T1_STOP_FILE"); stop != "" {
			if _, err := os.Stat(stop); err == nil {
				t.Fatalf("stopped by %s before block %d", stop, first)
			}
		}
		last := first + 127
		if last > end {
			last = end
		}
		blocks := make(types.Blocks, 0, last-first+1)
		for number := first; number <= last; number++ {
			hash := rawdb.ReadCanonicalHash(source, number)
			block := rawdb.ReadBlock(source, hash, number)
			if block == nil || block.Hash() != hash {
				t.Fatalf("missing or inconsistent source block %d", number)
			}
			blocks = append(blocks, block)
		}
		if index, err := chain.InsertChain(blocks); err != nil {
			t.Fatalf("replay failed at block %d: %v", first+uint64(index), err)
		}
		if chain.CurrentBlock().Hash() != blocks[len(blocks)-1].Hash() {
			t.Fatalf("head did not advance to %d", last)
		}
		if time.Since(lastLog) >= time.Minute {
			done := last - start.NumberU64()
			rate := float64(done) / time.Since(began).Seconds()
			t.Logf("progress height=%d blocks=%d rate=%.0f/s eta=%s", last, done, rate, time.Duration(float64(end-last)/rate)*time.Second)
			lastLog = time.Now()
		}
		first = last + 1
	}
	final := chain.CurrentBlock()
	want := rawdb.ReadHeader(source, rawdb.ReadCanonicalHash(source, end), end)
	if final.NumberU64() != end || final.Hash() != want.Hash() || final.Root() != want.Root || final.MixDigest() != want.MixDigest || final.ReceiptHash() != want.ReceiptHash {
		t.Fatalf("final block differs from the preserved tip")
	}
	statedb, err := chain.State()
	requireNoError(t, err)
	tickets, err := statedb.AllTickets()
	requireNoError(t, err)
	requireNoError(t, state.AddCachedTickets(final.MixDigest(), tickets))
	t.Logf("T1 MATCHED height=%d hash=%s root=%s ticketCommitment=%s receipts=%s tickets=%d elapsed=%s", end, final.Hash().Hex(), final.Root().Hex(), final.MixDigest().Hex(), final.ReceiptHash().Hex(), tickets.NumberOfTickets(), time.Since(began).Round(time.Second))
}
