package restart

import (
	"context"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestRestartAnchorStartupCost(t *testing.T) {
	if os.Getenv("FUSION_RESTART_ANCHOR_STARTUP") != "1" {
		t.Skip("bounded startup measurement requires explicit opt-in")
	}
	if mode := os.Getenv("FUSION_ANCHOR_STARTUP_CHILD"); mode != "" {
		measureAnchorStartup(t, mode)
		return
	}
	for _, depth := range []int{10000, 100000, 1000000} {
		t.Run(strconv.Itoa(depth), func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "chaindata")
			prepareAnchorStartup(t, path, depth)
			for _, mode := range []string{"disabled", "aligned", "split", "damaged_index"} {
				t.Run(mode, func(t *testing.T) {
					ctx, cancel := context.WithTimeout(context.Background(), 150*time.Second)
					defer cancel()
					command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartAnchorStartupCost$", "-test.v", "-test.timeout=140s")
					command.Env = append(os.Environ(), "FUSION_ANCHOR_STARTUP_CHILD="+mode, "FUSION_ANCHOR_STARTUP_PATH="+path, "FUSION_ANCHOR_STARTUP_DEPTH="+strconv.Itoa(depth))
					output, err := command.CombinedOutput()
					t.Logf("fresh-process startup %s:\n%s", mode, output)
					requireNoError(t, err)
				})
			}
		})
	}
}

func prepareAnchorStartup(t *testing.T, path string, depth int) {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "", false)
	requireNoError(t, err)
	f := newFixtureInDatabase(t, 0, db)
	f.chain.Stop()
	parent := f.parent.Header()
	anchorHeight := parent.Number.Uint64()
	batch := db.NewBatch()
	for i := 1; i <= depth; i++ {
		header := types.CopyHeader(parent)
		header.ParentHash = parent.Hash()
		header.Number = new(big.Int).Add(parent.Number, common.Big1)
		header.Time += 15
		header.Difficulty = big.NewInt(1)
		block := types.NewBlockWithHeader(header)
		rawdb.WriteBlock(batch, block)
		rawdb.WriteCanonicalHash(batch, block.Hash(), block.NumberU64())
		rawdb.WriteTd(batch, block.Hash(), block.NumberU64(), big.NewInt(int64(i+1)))
		if i%1024 == 0 {
			requireNoError(t, batch.Write())
			batch.Reset()
		}
		parent = header
	}
	rawdb.WriteHeadBlockHash(batch, parent.Hash())
	rawdb.WriteHeadHeaderHash(batch, parent.Hash())
	rawdb.WriteHeadFastBlockHash(batch, parent.Hash())
	requireNoError(t, batch.Write())
	requireNoError(t, db.Close())
	var bytes int64
	requireNoError(t, filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			bytes += info.Size()
		}
		return nil
	}))
	if bytes > 512<<20 {
		t.Fatalf("fixture exceeded 512 MiB: %d", bytes)
	}
	t.Logf("unsigned stored-header fixture: anchor=%d descendants=%d diskBytes=%d; state reused, no execution or seal-validation claim", anchorHeight, depth, bytes)
}

func measureAnchorStartup(t *testing.T, mode string) {
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	depth, err := strconv.ParseUint(os.Getenv("FUSION_ANCHOR_STARTUP_DEPTH"), 10, 64)
	requireNoError(t, err)
	if depth != 10000 && depth != 100000 && depth != 1000000 {
		t.Fatal("unsupported fixture depth")
	}
	plain, err := rawdb.NewLevelDBDatabase(os.Getenv("FUSION_ANCHOR_STARTUP_PATH"), 16, 16, "", false)
	requireNoError(t, err)
	db := &anchorHeaderReads{Database: plain}
	defer func() { db.Close() }()
	head := rawdb.ReadHeadHeaderHash(db)
	number := rawdb.ReadHeaderNumber(db, head)
	if number == nil || *number < depth {
		t.Fatal("missing fixture head")
	}
	anchorHeight := *number - depth
	config := *params.MainnetChainConfig
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: rawdb.ReadCanonicalHash(db, 0), ChainID: config.ChainID.Uint64(), Number: anchorHeight, Hash: rawdb.ReadCanonicalHash(db, anchorHeight)}
	expectedFull, expectedFast := head, head
	switch mode {
	case "disabled":
		config.RestartAnchor = nil
	case "aligned":
	case "split":
		expectedFull = rawdb.ReadCanonicalHash(db, anchorHeight+depth/2)
		expectedFast = rawdb.ReadCanonicalHash(db, anchorHeight+3*depth/4)
		rawdb.WriteHeadBlockHash(db, expectedFull)
		rawdb.WriteHeadFastBlockHash(db, expectedFast)
		defer rawdb.WriteHeadBlockHash(db, head)
		defer rawdb.WriteHeadFastBlockHash(db, head)
	case "damaged_index":
		original := rawdb.ReadCanonicalHash(db, anchorHeight+1)
		rawdb.WriteCanonicalHash(db, common.HexToHash("0xbad"), anchorHeight+1)
		defer rawdb.WriteCanonicalHash(db, original, anchorHeight+1)
	default:
		t.Fatalf("unknown startup case %q", mode)
	}
	before := databaseDigest(t, db)
	genesisHeader := rawdb.ReadHeader(db, rawdb.ReadCanonicalHash(db, 0), 0)
	genesis := &core.Genesis{Config: &config, GasLimit: genesisHeader.GasLimit, Difficulty: big.NewInt(1)}
	requireNoError(t, db.Close())
	db.Database, err = rawdb.NewLevelDBDatabase(os.Getenv("FUSION_ANCHOR_STARTUP_PATH"), 16, 16, "", false)
	requireNoError(t, err)
	runtime.GC()
	var initial, final runtime.MemStats
	runtime.ReadMemStats(&initial)
	db.reads.Store(0)
	started := time.Now()
	_, _, setupErr := core.SetupGenesisBlock(db, genesis)
	setupElapsed := time.Since(started)
	setupReads := db.reads.Load()
	started = time.Now()
	engine := datong.New(config.DaTong, db)
	chain, chainErr := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, engine, vm.Config{}, nil)
	chainElapsed := time.Since(started)
	if chain != nil {
		defer chain.Stop()
	}
	runtime.ReadMemStats(&final)
	reads := db.reads.Load()
	t.Logf("startup mode=%s descendants=%d setup=%s chain=%s setupHeaderReads=%d chainHeaderReads=%d allocatedBytes=%d goSysBytes=%d", mode, depth, setupElapsed, chainElapsed, setupReads, reads-setupReads, final.TotalAlloc-initial.TotalAlloc, final.Sys)
	if setupElapsed+chainElapsed > 120*time.Second || reads > 8*(depth+1)+256 || final.Sys > 512<<20 {
		t.Fatal("startup exceeded the declared time, linear-read or Go-memory bound")
	}
	if mode == "damaged_index" {
		message := fmt.Sprintf("restart anchor: inconsistent canonical index at %d", anchorHeight+1)
		requireErrorContains(t, setupErr, message)
		requireErrorContains(t, chainErr, message)
		if chain != nil {
			t.Fatal("damaged startup returned a usable chain")
		}
	} else {
		requireNoError(t, setupErr)
		requireNoError(t, chainErr)
		if chain.CurrentHeader().Hash() != head || chain.CurrentBlock().Hash() != expectedFull || chain.CurrentFastBlock().Hash() != expectedFast {
			t.Fatal("startup changed the expected heads")
		}
		if mode != "disabled" {
			requireNoError(t, chain.CheckRestartReady())
		}
	}
	requireDatabaseUnchanged(t, db, before)
}
