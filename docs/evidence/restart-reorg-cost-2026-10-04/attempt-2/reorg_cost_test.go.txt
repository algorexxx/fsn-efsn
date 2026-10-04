package restart

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/params"
)

type reorgCostManifest struct {
	Anchor   *types.Header
	OldTip   common.Hash
	NewTip   common.Hash
	OldCount int
	NewCount int
}

func TestRestartReorganizationCost(t *testing.T) {
	if os.Getenv("FUSION_RESTART_REORG_COST") != "1" {
		t.Skip("bounded reorganization measurement requires explicit opt-in")
	}
	if action := os.Getenv("FUSION_REORG_COST_CHILD"); action != "" {
		log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
		path := os.Getenv("FUSION_REORG_COST_PATH")
		depth, err := strconv.Atoi(os.Getenv("FUSION_REORG_COST_DEPTH"))
		requireNoError(t, err)
		if depth != 1024 && depth != 4096 {
			t.Fatal("unsupported reorganization depth")
		}
		shape := os.Getenv("FUSION_REORG_COST_SHAPE")
		if shape != "longer" && shape != "shorter" {
			t.Fatal("unsupported replacement shape")
		}
		switch action {
		case "prepare":
			prepareReorgCost(t, path, depth, shape)
		case "write":
			measureReorgCost(t, path)
		case "verify":
			verifyReorgCost(t, path)
		default:
			t.Fatal("unknown reorganization action")
		}
		return
	}
	for _, depth := range []int{1024, 4096} {
		for _, shape := range []string{"longer", "shorter"} {
			phases := []string{"complete"}
			if depth == 4096 && shape == "shorter" {
				phases = append(phases, "before", "after")
			}
			for _, phase := range phases {
				t.Run(fmt.Sprintf("%d_%s_%s", depth, shape, phase), func(t *testing.T) {
					path := t.TempDir()
					for _, action := range []string{"prepare", "write", "verify"} {
						runReorgCostChild(t, path, depth, shape, phase, action)
					}
				})
			}
		}
	}
}

func runReorgCostChild(t *testing.T, path string, depth int, shape, phase, action string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 210*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartReorganizationCost$", "-test.v", "-test.timeout=200s")
	command.Env = append(os.Environ(), "FUSION_REORG_COST_CHILD="+action, "FUSION_REORG_COST_PATH="+path,
		"FUSION_REORG_COST_DEPTH="+strconv.Itoa(depth), "FUSION_REORG_COST_SHAPE="+shape, "FUSION_REORG_COST_PHASE="+phase)
	output, err := command.CombinedOutput()
	t.Logf("%s:\n%s", action, output)
	if action == "write" && phase != "complete" {
		var exit *exec.ExitError
		if !errors.As(err, &exit) || exit.ExitCode() != 86 || !strings.Contains(string(output), "CRASH "+phase+" canonical batch") || ctx.Err() != nil {
			t.Fatalf("expected exact canonical-batch exit, got %v", err)
		}
		return
	}
	requireNoError(t, err)
}

func readReorgCostManifest(t *testing.T, path string) *reorgCostManifest {
	t.Helper()
	data, err := os.ReadFile(filepath.Join(path, "manifest.json"))
	requireNoError(t, err)
	var manifest reorgCostManifest
	requireNoError(t, json.Unmarshal(data, &manifest))
	return &manifest
}

func reorgCostConfig(db ethdb.Database, manifest *reorgCostManifest) *params.ChainConfig {
	config := *params.MainnetChainConfig
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: rawdb.ReadCanonicalHash(db, 0), ChainID: config.ChainID.Uint64(), Number: manifest.Anchor.Number.Uint64(), Hash: manifest.Anchor.Hash()}
	return &config
}

func measureReorgCost(t *testing.T, path string) {
	manifest := readReorgCostManifest(t, path)
	plain, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	defer plain.Close()
	db := &reorgCostDatabase{Database: plain, phase: os.Getenv("FUSION_REORG_COST_PHASE")}
	config := reorgCostConfig(db, manifest)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, datong.New(config.DaTong, db), vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	if chain.CurrentBlock().Hash() != manifest.OldTip {
		t.Fatal("measurement must start on the complete old branch")
	}
	head := rawdb.ReadBlock(db, manifest.NewTip, manifest.Anchor.Number.Uint64()+uint64(manifest.NewCount))
	receipts := rawdb.ReadReceipts(db, head.Hash(), head.NumberU64(), config)
	state, err := chain.StateAt(head.Root(), head.MixDigest())
	requireNoError(t, err)
	oldTD := chain.GetTd(manifest.OldTip, manifest.Anchor.Number.Uint64()+uint64(manifest.OldCount))
	newTD := chain.GetTd(head.ParentHash(), head.NumberU64()-1)
	if new(big.Int).Add(newTD, head.Difficulty()).Cmp(oldTD) <= 0 {
		t.Fatal("replacement must be strictly heavier")
	}
	runtime.GC()
	var initial, final runtime.MemStats
	runtime.ReadMemStats(&initial)
	db.started = time.Now()
	db.armed = true
	status, err := chain.WriteBlockWithState(head, receipts, state)
	elapsed := time.Since(db.started)
	db.armed = false
	runtime.ReadMemStats(&final)
	requireNoError(t, err)
	if status != core.CanonStatTy || chain.CurrentBlock().Hash() != manifest.NewTip || db.switches != 1 || elapsed > 120*time.Second {
		t.Fatal("canonical switch did not satisfy its result, single-batch or time bound")
	}
	t.Logf("reorganization old=%d new=%d duration=%s allocatedBytes=%d heapAfterBytes=%d goSysAfterBytes=%d", manifest.OldCount, manifest.NewCount, elapsed, final.TotalAlloc-initial.TotalAlloc, final.HeapAlloc, final.Sys)
}

type reorgCostDatabase struct {
	ethdb.Database
	armed    bool
	phase    string
	started  time.Time
	switches int
}

func (db *reorgCostDatabase) NewBatch() ethdb.Batch {
	b := &reorgCostBatch{db: db}
	b.Batch = ethdb.HookedBatch{Batch: db.Database.NewBatch(), OnPut: b.recordPut, OnDelete: b.recordDelete}
	return b
}

type reorgCostBatch struct {
	ethdb.Batch
	db             *reorgCostDatabase
	payloadBytes   int
	canonicalPuts  int
	canonicalDrops int
	lookupPuts     int
	lookupDrops    int
	markers        byte
}

func (b *reorgCostBatch) recordPut(key, value []byte) {
	b.payloadBytes += len(key) + len(value)
	switch crashKeyName(key) {
	case "canonical":
		b.canonicalPuts++
	case "tx-lookup":
		b.lookupPuts++
	case "LastBlock":
		b.markers |= 1
	case "LastHeader":
		b.markers |= 2
	case "LastFast":
		b.markers |= 4
	}
}

func (b *reorgCostBatch) recordDelete(key []byte) {
	b.payloadBytes += len(key)
	switch crashKeyName(key) {
	case "canonical":
		b.canonicalDrops++
	case "tx-lookup":
		b.lookupDrops++
	}
}

func (b *reorgCostBatch) Write() error {
	if !b.db.armed || b.canonicalPuts < 2 {
		return b.Batch.Write()
	}
	var memory runtime.MemStats
	runtime.ReadMemStats(&memory)
	elapsed := time.Since(b.db.started)
	fmt.Printf("canonical batch: puts=%d drops=%d lookupPuts=%d lookupDrops=%d markers=%d keyValueBytes=%d apiValueSize=%d stagedHeapBytes=%d goSysBytes=%d elapsed=%s\n", b.canonicalPuts, b.canonicalDrops, b.lookupPuts, b.lookupDrops, b.markers, b.payloadBytes, b.ValueSize(), memory.HeapAlloc, memory.Sys, elapsed)
	if b.markers != 7 || b.payloadBytes > 64<<20 || memory.HeapAlloc > 1<<30 || memory.Sys > 1536<<20 || elapsed > 120*time.Second {
		return fmt.Errorf("canonical switch exceeded its declared batch, memory, time or marker bound")
	}
	b.db.switches++
	if b.db.phase == "before" {
		fmt.Println("CRASH before canonical batch")
		os.Exit(86)
	}
	if err := b.Batch.Write(); err != nil {
		return err
	}
	if b.db.phase == "after" {
		fmt.Println("CRASH after canonical batch")
		os.Exit(86)
	}
	return nil
}

func (b *reorgCostBatch) Reset() {
	b.Batch.Reset()
	b.payloadBytes, b.canonicalPuts, b.canonicalDrops = 0, 0, 0
	b.lookupPuts, b.lookupDrops, b.markers = 0, 0, 0
}
