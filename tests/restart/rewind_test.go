package restart

import (
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
)

func verifyCrashRewind(t *testing.T, db ethdb.Database, chain *core.BlockChain, history *crashHistory, scenario string) {
	t.Helper()
	oldTip, target := history.Old[len(history.Old)-1], history.New[len(history.New)-1]
	header := rawdb.ReadHeadHeaderHash(db)
	full, fast := header, header
	if header != oldTip.Hash() && header != target.Hash() {
		t.Fatalf("partial rewind published: header=%s old=%s target=%s", header.Hex(), oldTip.Hash().Hex(), target.Hash().Hex())
	}
	if scenario == "rewind_split" {
		full = history.Old[0].Hash()
		if header == oldTip.Hash() {
			fast = history.Old[2].Hash()
		}
	}
	if header == target.Hash() {
		switch scenario {
		case "rewind_pruned":
			full = history.Old[0].Hash()
		case "rewind_missing_body":
			full, fast = chain.Genesis().Hash(), chain.Genesis().Hash()
		case "rewind_missing_ancestor":
			full = chain.Genesis().Hash()
		}
	}
	if rawdb.ReadHeadBlockHash(db) != full || rawdb.ReadHeadFastBlockHash(db) != fast || chain.CurrentBlock().Hash() != full || chain.CurrentFastBlock().Hash() != fast || chain.CurrentHeader().Hash() != header {
		t.Fatal("rewind head markers disagree or cold startup repaired them")
	}
	belowAnchor := chain.CurrentBlock().NumberU64() < history.Anchor.NumberU64()
	if err := chain.CheckRestartReady(); (err != nil) != belowAnchor {
		t.Fatalf("unexpected rewind readiness: below anchor=%t err=%v", belowAnchor, err)
	}
	_, err := chain.State()
	requireNoError(t, err)
	for _, block := range append(types.Blocks{history.Anchor}, history.Old...) {
		present := header == oldTip.Hash() || block.NumberU64() <= target.NumberU64()
		want := common.Hash{}
		if present {
			want = block.Hash()
		}
		if rawdb.ReadCanonicalHash(db, block.NumberU64()) != want || (rawdb.ReadHeader(db, block.Hash(), block.NumberU64()) != nil) != present {
			t.Fatalf("rewind left inconsistent header data at %d", block.NumberU64())
		}
		bodyPresent := present && !(scenario == "rewind_missing_body" && block.Hash() == history.Old[1].Hash()) && !(scenario == "rewind_missing_ancestor" && block.Hash() == history.Old[0].Hash())
		if (rawdb.ReadBlock(db, block.Hash(), block.NumberU64()) != nil) != bodyPresent {
			t.Fatalf("rewind left inconsistent block data at %d", block.NumberU64())
		}
		for _, tx := range block.Transactions() {
			found, _, _, _ := rawdb.ReadTransaction(db, tx.Hash())
			if (found != nil) != bodyPresent {
				t.Fatalf("rewind transaction resolution disagrees at %d", block.NumberU64())
			}
		}
	}
	requireNoError(t, chain.SetHead(target.NumberU64()))
	if chain.CurrentHeader().Hash() != target.Hash() {
		t.Fatal("resumed rewind missed its target")
	}
	if chain.CurrentBlock().NumberU64() == 0 {
		requireNoError(t, chain.FastSyncCommitHead(history.Parent.Hash()))
		if chain.CheckRestartReady() == nil {
			t.Fatal("retained pre-anchor state pivot enabled mining")
		}
	}
	_, err = chain.InsertChain(append(types.Blocks{history.Anchor}, history.Old...))
	requireNoError(t, err)
	if chain.CurrentBlock().Hash() != oldTip.Hash() || chain.CurrentHeader().Hash() != oldTip.Hash() || chain.CurrentFastBlock().Hash() != oldTip.Hash() {
		t.Fatal("rewind recovery did not restore the original valid tip")
	}
	requireNoError(t, chain.CheckRestartReady())
	restored := *history
	restored.New = history.Old
	requireCrashIndexes(t, db, &restored, history.Old)
}
