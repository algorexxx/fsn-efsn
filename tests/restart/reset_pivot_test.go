package restart

import (
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

func verifyCrashReset(t *testing.T, db ethdb.Database, chain *core.BlockChain, history *crashHistory) {
	t.Helper()
	genesis, oldTip := history.New[0], history.Old[len(history.Old)-1]
	head := rawdb.ReadHeadBlockHash(db)
	if head != genesis.Hash() && head != oldTip.Hash() {
		t.Fatal("reset published neither original nor genesis head")
	}
	if rawdb.ReadHeadHeaderHash(db) != head || rawdb.ReadHeadFastBlockHash(db) != head || chain.CurrentBlock().Hash() != head || chain.CurrentHeader().Hash() != head || chain.CurrentFastBlock().Hash() != head {
		t.Fatal("reset persisted inconsistent heads or startup repaired them")
	}
	reset := head == genesis.Hash()
	if err := chain.CheckRestartReady(); (err != nil) != reset {
		t.Fatalf("unexpected reset readiness: reset=%t err=%v", reset, err)
	}
	if chain.Genesis().Hash() != genesis.Hash() || rawdb.ReadCanonicalHash(db, 0) != genesis.Hash() || chain.RestartAnchorHeight() != history.Anchor.NumberU64() {
		t.Fatal("reset changed genesis or removed the configured anchor")
	}
	_, err := chain.State()
	requireNoError(t, err)
	for _, block := range append(types.Blocks{history.Parent, history.Anchor}, history.Old...) {
		want := block.Hash()
		if reset {
			want = common.Hash{}
		}
		if rawdb.ReadCanonicalHash(db, block.NumberU64()) != want || (rawdb.ReadBlock(db, block.Hash(), block.NumberU64()) == nil) != reset {
			t.Fatalf("reset left inconsistent canonical data at %d", block.NumberU64())
		}
		for _, tx := range block.Transactions() {
			found, _, _, _ := rawdb.ReadTransaction(db, tx.Hash())
			if (found == nil) != reset {
				t.Fatalf("reset transaction resolution disagrees at %d", block.NumberU64())
			}
		}
	}
	requireNoError(t, chain.Reset())
	requireNoError(t, chain.Reset())
	if chain.CurrentBlock().Hash() != genesis.Hash() || chain.CurrentHeader().Hash() != genesis.Hash() || chain.CurrentFastBlock().Hash() != genesis.Hash() {
		t.Fatal("reset resume did not preserve genesis heads")
	}
	requireErrorContains(t, chain.CheckRestartReady(), "synchronization required")
	before := databaseDigest(t, db)
	header := genesis.Header()
	header.Time++
	requireErrorContains(t, chain.ResetWithGenesisBlock(types.NewBlockWithHeader(header)), "cannot replace genesis")
	requireDatabaseUnchanged(t, db, before)
}

func verifyCrashPivot(t *testing.T, db ethdb.Database, chain *core.BlockChain, history *crashHistory) {
	t.Helper()
	genesis, target, tip := chain.Genesis(), history.New[0], history.Old[len(history.Old)-1]
	head := rawdb.ReadHeadBlockHash(db)
	if head != genesis.Hash() && head != target.Hash() {
		t.Fatal("pivot published neither original nor target full head")
	}
	if rawdb.ReadHeadHeaderHash(db) != tip.Hash() || rawdb.ReadHeadFastBlockHash(db) != tip.Hash() || chain.CurrentBlock().Hash() != head || chain.CurrentHeader().Hash() != tip.Hash() || chain.CurrentFastBlock().Hash() != tip.Hash() {
		t.Fatal("pivot changed header/fast heads or startup repaired full head")
	}
	ready := head == target.Hash() && target.NumberU64() >= history.Anchor.NumberU64()
	if err := chain.CheckRestartReady(); (err == nil) != ready {
		t.Fatalf("unexpected pivot readiness: ready=%t err=%v", ready, err)
	}
	statedb, err := chain.State()
	requireNoError(t, err)
	if head == target.Hash() {
		tickets, err := statedb.AllTickets()
		requireNoError(t, err)
		if tickets.NumberOfTickets() != 1 {
			t.Fatal("pivot lost the target ticket state")
		}
	}
	indexed := *history
	indexed.New = history.Old
	requireCrashIndexes(t, db, &indexed, history.Old)
	requireNoError(t, chain.FastSyncCommitHead(target.Hash()))
	requireNoError(t, chain.FastSyncCommitHead(target.Hash()))
	if chain.CurrentBlock().Hash() != target.Hash() || rawdb.ReadHeadBlockHash(db) != target.Hash() {
		t.Fatal("pivot resume missed its target")
	}
	_, err = chain.InsertChain(append(types.Blocks{history.Anchor}, history.Old...))
	requireNoError(t, err)
	if chain.CurrentBlock().Hash() != tip.Hash() || rawdb.ReadHeadBlockHash(db) != tip.Hash() {
		t.Fatal("pivot could not continue through the accepted suffix")
	}
	requireNoError(t, chain.CheckRestartReady())
	requireCrashIndexes(t, db, &indexed, history.Old)
}

func verifyCrashReceiptPivot(t *testing.T, db ethdb.Database, chain *core.BlockChain, history *crashHistory) {
	t.Helper()
	tip, previous := history.Old[3], history.Old[2]
	full, fast := rawdb.ReadHeadBlockHash(db), rawdb.ReadHeadFastBlockHash(db)
	bodyPresent := rawdb.ReadBlock(db, tip.Hash(), tip.NumberU64()) != nil
	if full != history.Parent.Hash() && full != tip.Hash() || fast != previous.Hash() && fast != tip.Hash() {
		t.Fatal("receipt/pivot sequence published unexpected heads")
	}
	if full == tip.Hash() && fast != tip.Hash() || !bodyPresent && (full != history.Parent.Hash() || fast != previous.Hash()) {
		t.Fatal("receipt/pivot sequence published heads ahead of available data")
	}
	if rawdb.ReadHeadHeaderHash(db) != tip.Hash() || chain.CurrentBlock().Hash() != full || chain.CurrentFastBlock().Hash() != fast || chain.CurrentHeader().Hash() != tip.Hash() {
		t.Fatal("startup repaired an interrupted receipt/pivot sequence")
	}
	if err := chain.CheckRestartReady(); (err == nil) != (full == tip.Hash()) {
		t.Fatalf("unexpected receipt/pivot readiness: %v", err)
	}
	indexed := *history
	if !bodyPresent {
		indexed.Old = history.Old[:3]
	}
	indexed.New = indexed.Old
	requireCrashIndexes(t, db, &indexed, indexed.Old)
	if rawdb.ReadCanonicalHash(db, tip.NumberU64()) != tip.Hash() {
		t.Fatal("receipt insertion changed canonical header index")
	}
	for _, tx := range tip.Transactions() {
		lookup := rawdb.ReadTxLookupEntry(db, tx.Hash())
		receipt, _, _, _ := rawdb.ReadReceipt(db, tx.Hash(), params.MainnetChainConfig)
		if (lookup != nil) != bodyPresent || (receipt != nil) != bodyPresent {
			t.Fatal("receipt insertion split body, receipt and lookup persistence")
		}
	}
	_, err := chain.InsertReceiptChain(history.New, []types.Receipts{history.Receipts}, 0)
	requireNoError(t, err)
	requireNoError(t, chain.FastSyncCommitHead(tip.Hash()))
	verifyCrashPivot(t, db, chain, history)
}
