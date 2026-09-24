package restart

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
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
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type crashHistory struct {
	Anchor *types.Block
	Old    types.Blocks
	New    types.Blocks
}

type crashDatabase struct {
	ethdb.Database
	mu     sync.Mutex
	armed  bool
	cut    int
	phase  string
	events []string
}

func (db *crashDatabase) write(label string, write func() error) error {
	db.mu.Lock()
	defer db.mu.Unlock()
	if !db.armed {
		return write()
	}
	db.events = append(db.events, label)
	if len(db.events) == db.cut && db.phase == "before" {
		fmt.Printf("CRASH before write %d: %s\n", db.cut, label)
		os.Exit(86)
	}
	err := write()
	if err == nil && len(db.events) == db.cut && db.phase == "after" {
		fmt.Printf("CRASH after write %d: %s\n", db.cut, label)
		os.Exit(86)
	}
	return err
}

func (db *crashDatabase) Put(key, value []byte) error {
	return db.write("put:"+crashKeyName(key), func() error { return db.Database.Put(key, value) })
}

func (db *crashDatabase) Delete(key []byte) error {
	return db.write("delete:"+crashKeyName(key), func() error { return db.Database.Delete(key) })
}

func (db *crashDatabase) NewBatch() ethdb.Batch {
	b := &crashBatch{db: db}
	b.Batch = ethdb.HookedBatch{Batch: db.Database.NewBatch(), OnPut: b.note, OnDelete: func(key []byte) { b.note(key, nil) }}
	return b
}

type crashBatch struct {
	ethdb.Batch
	db    *crashDatabase
	names []string
}

func (b *crashBatch) note(key, _ []byte) {
	name := crashKeyName(key)
	for _, existing := range b.names {
		if existing == name {
			return
		}
	}
	b.names = append(b.names, name)
}

func (b *crashBatch) Write() error {
	return b.db.write("batch:"+strings.Join(b.names, ","), b.Batch.Write)
}

func (b *crashBatch) Reset() {
	b.Batch.Reset()
	b.names = nil
}

func crashKeyName(key []byte) string {
	switch string(key) {
	case "LastBlock", "LastHeader", "LastFast":
		return string(key)
	}
	if len(key) == 10 && key[0] == 'h' && key[9] == 'n' {
		return "canonical"
	}
	if len(key) == 33 && key[0] == 'l' {
		return "tx-lookup"
	}
	return "data"
}

func TestRestartCrashBoundaries(t *testing.T) {
	if os.Getenv("FUSION_RESTART_CRASH_REHEARSAL") != "1" {
		t.Skip("opt-in subprocess crash-boundary rehearsal uses disposable LevelDB databases")
	}
	if action := os.Getenv("FUSION_RESTART_CRASH_CHILD"); action != "" {
		log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
		datong.InitCheckPoints("")
		path, scenario := os.Getenv("FUSION_RESTART_CRASH_PATH"), os.Getenv("FUSION_RESTART_CRASH_SCENARIO")
		if action == "verify" {
			verifyCrashDatabase(t, path, scenario)
		} else {
			writeCrashDatabase(t, path, scenario)
		}
		return
	}
	for _, scenario := range []string{"linear", "reorg", "rollback"} {
		t.Run(scenario, func(t *testing.T) {
			trace := t.TempDir()
			runCrashChild(t, trace, scenario, "write", 0, "", false)
			runCrashChild(t, trace, scenario, "verify", 0, "", false)
			data, err := os.ReadFile(filepath.Join(trace, "writes.json"))
			requireNoError(t, err)
			var events []string
			requireNoError(t, json.Unmarshal(data, &events))
			if len(events) == 0 {
				t.Fatal("no database write boundaries recorded")
			}
			t.Logf("successful %s write trace: %v", scenario, events)
			for i, event := range events {
				for _, phase := range []string{"before", "after"} {
					t.Run(fmt.Sprintf("%02d_%s", i+1, phase), func(t *testing.T) {
						path := t.TempDir()
						runCrashChild(t, path, scenario, "write", i+1, phase, true)
						runCrashChild(t, path, scenario, "verify", 0, "", false)
						t.Logf("consistent cold reopen and resume: %s write %d %s (%s)", scenario, i+1, phase, event)
					})
				}
			}
		})
	}
}

func runCrashChild(t *testing.T, path, scenario, action string, cut int, phase string, crash bool) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartCrashBoundaries$", "-test.v", "-test.timeout=30s")
	command.Env = append(os.Environ(), "FUSION_RESTART_CRASH_CHILD="+action, "FUSION_RESTART_CRASH_PATH="+path,
		"FUSION_RESTART_CRASH_SCENARIO="+scenario, "FUSION_RESTART_CRASH_CUT="+strconv.Itoa(cut), "FUSION_RESTART_CRASH_PHASE="+phase)
	output, err := command.CombinedOutput()
	if strings.Contains(string(output), "WARNING: DATA RACE") {
		t.Fatalf("crash child race: %s", output)
	}
	if crash {
		var exit *exec.ExitError
		if !errors.As(err, &exit) || exit.ExitCode() != 86 || !strings.Contains(string(output), "CRASH "+phase) || ctx.Err() != nil {
			t.Fatalf("expected abrupt write-boundary exit, got %v:\n%s", err, output)
		}
		return
	}
	if err != nil {
		t.Fatalf("%s %s child: %v\n%s", scenario, action, err, output)
	}
}

func writeCrashDatabase(t *testing.T, path, scenario string) {
	plain, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	db := &crashDatabase{Database: plain}
	f := newFixtureInDatabase(t, 0, db)
	builder := newFixture(t)
	advancePurchaseFixture(t, f, builder)
	anchor := buildAnchorBranch(t, f, 1, 120)[0]
	builder.importBlock(t, anchor)
	old := roundTripBlocks(t, buildAnchorBranch(t, f, 4, 120))
	history := crashHistory{Anchor: anchor, Old: old}
	config := *f.chain.Config()
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: f.chain.Genesis().Hash(), ChainID: config.ChainID.Uint64(), Number: anchor.NumberU64(), Hash: anchor.Hash()}
	f.chain.Stop()
	f.engine = datong.New(config.DaTong, db)
	f.chain, err = core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, f.engine, vm.Config{}, func(block *types.Block) bool { return block.Hash() == old[len(old)-1].Hash() })
	requireNoError(t, err)
	switch scenario {
	case "linear":
		block := f.buildBlockWithTransactions(t, f.chain.CurrentBlock().Time()+120, []*types.Transaction{f.signPurchase(t, f.chain.CurrentBlock().Time(), common.TimeLockForever)})
		history.New = append(append(types.Blocks{}, old...), roundTripBlocks(t, types.Blocks{block})[0])
	case "reorg":
		history.New = roundTripBlocks(t, buildAnchorBranch(t, builder, 5, 121))
		_, err = f.chain.InsertChain(history.New[:4])
		requireNoError(t, err)
		if f.chain.CurrentBlock().Hash() != old[3].Hash() || builder.chain.GetTd(history.New[4].Hash(), history.New[4].NumberU64()).Cmp(f.chain.GetTd(old[3].Hash(), old[3].NumberU64())) <= 0 {
			t.Fatal("reorg fixture did not preserve the old head before its heavier successor")
		}
	case "rollback":
		history.New = old[:2]
	default:
		t.Fatalf("unknown crash scenario %q", scenario)
	}
	encoded, err := rlp.EncodeToBytes(&history)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "history.rlp"), encoded, 0600))
	db.cut, err = strconv.Atoi(os.Getenv("FUSION_RESTART_CRASH_CUT"))
	requireNoError(t, err)
	db.phase = os.Getenv("FUSION_RESTART_CRASH_PHASE")
	db.armed = true
	if scenario == "rollback" {
		f.chain.Rollback([]common.Hash{old[2].Hash(), old[3].Hash()})
	} else {
		_, err = f.chain.InsertChain(history.New[len(history.New)-1:])
		requireNoError(t, err)
	}
	db.armed = false
	if db.cut != 0 {
		t.Fatalf("write boundary %d was not reached; trace=%v", db.cut, db.events)
	}
	data, err := json.MarshalIndent(db.events, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "writes.json"), data, 0600))
}

func verifyCrashDatabase(t *testing.T, path, scenario string) {
	data, err := os.ReadFile(filepath.Join(path, "history.rlp"))
	requireNoError(t, err)
	var history crashHistory
	requireNoError(t, rlp.DecodeBytes(data, &history))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	defer db.Close()
	head := rawdb.ReadHeadBlockHash(db)
	config := *params.MainnetChainConfig
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: rawdb.ReadCanonicalHash(db, 0), ChainID: config.ChainID.Uint64(), Number: history.Anchor.NumberU64(), Hash: history.Anchor.Hash()}
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	t.Logf("cold startup: head=%s readiness=%v", chain.CurrentBlock().Hash().Hex(), chain.CheckRestartReady())
	oldTip, newTip := history.Old[len(history.Old)-1], history.New[len(history.New)-1]
	expected := history.Old
	if head == newTip.Hash() {
		expected = history.New
	} else if head != oldTip.Hash() {
		t.Fatalf("partial chain published: head=%s, old=%s, new=%s", head.Hex(), oldTip.Hash().Hex(), newTip.Hash().Hex())
	}
	if rawdb.ReadHeadHeaderHash(db) != head || rawdb.ReadHeadFastBlockHash(db) != head {
		t.Fatal("persisted head markers disagree after interruption")
	}
	indexed := expected
	if scenario == "rollback" {
		indexed = history.Old
	}
	requireCrashIndexes(t, db, &history, indexed)
	if chain.CurrentBlock().Hash() != head || chain.CurrentHeader().Hash() != head || chain.CurrentFastBlock().Hash() != head {
		t.Fatal("startup repaired an inconsistent interrupted operation")
	}
	requireNoError(t, chain.CheckRestartReady())
	state, err := chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTickets() != 1 {
		t.Fatal("interrupted operation lost its available ticket state")
	}
	if scenario == "rollback" {
		if head == oldTip.Hash() {
			chain.Rollback([]common.Hash{history.Old[2].Hash(), history.Old[3].Hash()})
		}
		_, err = chain.InsertChain(history.Old[2:])
		requireNoError(t, err)
		if chain.CurrentBlock().Hash() != oldTip.Hash() {
			t.Fatal("rollback recovery did not restore the original valid tip")
		}
	} else {
		_, err = chain.InsertChain(history.New[len(history.New)-1:])
		requireNoError(t, err)
		if chain.CurrentBlock().Hash() != newTip.Hash() {
			t.Fatal("reimport did not recover the complete successor")
		}
		requireCrashIndexes(t, db, &history, history.New)
	}
}

func requireCrashIndexes(t *testing.T, db ethdb.Database, history *crashHistory, expected types.Blocks) {
	t.Helper()
	canonical := map[uint64]common.Hash{history.Anchor.NumberU64(): history.Anchor.Hash()}
	transactions := make(map[common.Hash]*types.Block)
	for _, block := range expected {
		canonical[block.NumberU64()] = block.Hash()
		for _, tx := range block.Transactions() {
			transactions[tx.Hash()] = block
		}
	}
	for _, block := range append(append(types.Blocks{history.Anchor}, history.Old...), history.New...) {
		if got := rawdb.ReadCanonicalHash(db, block.NumberU64()); got != canonical[block.NumberU64()] {
			t.Fatalf("partial canonical index at %d: have %s want %s", block.NumberU64(), got.Hex(), canonical[block.NumberU64()].Hex())
		}
		if block.Hash() == history.Anchor.Hash() {
			continue
		}
		for _, tx := range block.Transactions() {
			position := rawdb.ReadTxLookupEntry(db, tx.Hash())
			wanted := transactions[tx.Hash()]
			if wanted == nil {
				if position != nil {
					t.Fatalf("stale transaction lookup after interrupted switch: %s", tx.Hash().Hex())
				}
				continue
			}
			found, hash, number, _ := rawdb.ReadTransaction(db, tx.Hash())
			receipt, receiptHash, _, _ := rawdb.ReadReceipt(db, tx.Hash(), params.MainnetChainConfig)
			if found == nil || hash != wanted.Hash() || number != wanted.NumberU64() || receipt == nil || receiptHash != wanted.Hash() {
				t.Fatalf("missing or inconsistent canonical transaction/receipt: %s", tx.Hash().Hex())
			}
		}
	}
}
