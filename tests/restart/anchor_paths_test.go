package restart

import (
	"context"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func TestRestartAnchorEntryPointsCharacterization(t *testing.T) {
	if mode := os.Getenv("FUSION_ANCHOR_PATH_CHILD"); mode != "" {
		runAnchorPath(t, mode)
		return
	}
	for _, mode := range []string{"heavier_fork", "checkpoint_direct", "checkpoint_stored_fork", "checkpoint_headers", "checkpoint_receipts", "checkpoint_commit_head", "checkpoint_startup", "checkpoint_late_init", "checkpoint_body_shortcut"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartAnchorEntryPointsCharacterization$", "-test.v", "-test.timeout=40s")
			command.Env = append(os.Environ(), "FUSION_ANCHOR_PATH_CHILD="+mode)
			output, err := command.CombinedOutput()
			t.Logf("isolated anchor path %s:\n%s", mode, output)
			requireNoError(t, err)
		})
	}
}

func runAnchorPath(t *testing.T, mode string) {
	datong.InitCheckPoints("")
	receiver := newFixture(t)
	returning := newFixture(t)
	advancePurchaseFixture(t, receiver, returning)
	shared := receiver.chain.CurrentBlock()
	accepted := buildAnchorBranch(t, receiver, 4, 120)
	later := roundTripBlocks(t, buildAnchorBranch(t, returning, 5, 121))
	anchor, oldHead, newHead := accepted[0], accepted[3], later[4]
	oldTD := receiver.chain.GetTd(oldHead.Hash(), oldHead.NumberU64())
	newTD := returning.chain.GetTd(newHead.Hash(), newHead.NumberU64())
	if newTD.Cmp(oldTD) <= 0 || anchor.Hash() == later[0].Hash() {
		t.Fatal("fixture needs incompatible branches with strictly greater returning difficulty")
	}
	if rawdb.ReadCanonicalHash(receiver.db, anchor.NumberU64()) != anchor.Hash() {
		t.Fatal("accepted branch was not canonical before the experiment")
	}
	t.Logf("common=%d proposedAnchor=%s acceptedTD=%s returningTD=%s", shared.NumberU64(), anchor.Hash().Hex(), oldTD, newTD)
	switch mode {
	case "heavier_fork":
		_, err := receiver.chain.InsertChain(later)
		requireNoError(t, err)
		requireCanonicalTip(t, receiver, newHead)
		if rawdb.ReadCanonicalHash(receiver.db, anchor.NumberU64()) != later[0].Hash() {
			t.Fatal("heavier branch did not replace the proposed anchor")
		}
		transaction := accepted[3].Transactions()[0]
		if tx, _, _, _ := rawdb.ReadTransaction(receiver.db, transaction.Hash()); tx != nil {
			t.Fatal("displaced transaction still has a canonical lookup")
		}
		t.Log("ordinary full import replaced the accepted branch and removed its later transaction lookup")
	case "checkpoint_direct":
		setSyntheticCheckpoint(anchor)
		_, err := receiver.chain.InsertChain(later)
		requireErrorContains(t, err, "check point failed, block hash mismatch")
		requireCanonicalTip(t, receiver, oldHead)
		t.Log("control: an incoming batch containing the mismatching checkpoint height was rejected")
	case "checkpoint_stored_fork":
		_, err := receiver.chain.InsertChain(later[:1])
		requireNoError(t, err)
		requireCanonicalTip(t, receiver, oldHead)
		setSyntheticCheckpoint(anchor)
		heads := make(chan core.ChainHeadEvent, 8)
		subscription := receiver.chain.SubscribeChainHeadEvent(heads)
		defer subscription.Unsubscribe()
		_, err = receiver.chain.InsertChain(later[1:])
		requireErrorContains(t, err, "check point failed, block hash mismatch")
		requireCanonicalTip(t, receiver, oldHead)
		if receiver.chain.CurrentHeader().Hash() != oldHead.Hash() || receiver.chain.CurrentFastBlock().Hash() != oldHead.Hash() || rawdb.ReadHeadHeaderHash(receiver.db) != oldHead.Hash() || rawdb.ReadHeadFastBlockHash(receiver.db) != oldHead.Hash() {
			t.Fatal("rejected checkpoint fork changed a header or fast head")
		}
		for _, block := range accepted {
			if rawdb.ReadCanonicalHash(receiver.db, block.NumberU64()) != block.Hash() {
				t.Fatal("rejected checkpoint fork changed a canonical index")
			}
			for _, transaction := range block.Transactions() {
				found, hash, _, _ := rawdb.ReadTransaction(receiver.db, transaction.Hash())
				if found == nil || hash != block.Hash() {
					t.Fatal("rejected checkpoint fork changed an accepted transaction lookup")
				}
			}
		}
		select {
		case <-heads:
			t.Fatal("rejected checkpoint fork emitted a canonical head event")
		default:
		}
		requireLinkedAncestor(t, receiver, oldHead, anchor)
		limit := uint64(1024)
		indexedAncestor, number := receiver.chain.GetAncestor(oldHead.Hash(), oldHead.NumberU64(), oldHead.NumberU64()-anchor.NumberU64(), &limit)
		if indexedAncestor != anchor.Hash() || number != anchor.NumberU64() {
			t.Fatal("canonical ancestor index disagrees with the retained linked ancestry")
		}
		t.Log("stored checkpoint fork rejected before publishing canonical changes; all heads, accepted indexes, transaction lookups and linked ancestry retained")
	case "checkpoint_headers":
		_, err := receiver.chain.InsertHeaderChain(blockHeaders(later[:1]), 1)
		requireNoError(t, err)
		setSyntheticCheckpoint(anchor)
		_, err = receiver.chain.InsertHeaderChain(blockHeaders(later[1:]), 1)
		requireNoError(t, err)
		if receiver.chain.CurrentHeader().Hash() != newHead.Hash() || rawdb.ReadCanonicalHash(receiver.db, anchor.NumberU64()) != later[0].Hash() {
			t.Fatal("header path did not reproduce the incompatible canonical rewrite")
		}
		if receiver.chain.CurrentBlock().Hash() != oldHead.Hash() {
			t.Fatal("header-only import unexpectedly executed full blocks")
		}
		t.Log("header-only continuation above a stored incompatible checkpoint rewrote canonical header ancestry")
	case "checkpoint_receipts":
		_, err := receiver.chain.InsertHeaderChain(blockHeaders(later), 1)
		requireNoError(t, err)
		setSyntheticCheckpoint(anchor)
		receipts := make([]types.Receipts, len(later))
		for i, block := range later {
			receipts[i] = returning.chain.GetReceiptsByHash(block.Hash())
		}
		_, err = receiver.chain.InsertReceiptChain(later, receipts, 0)
		requireNoError(t, err)
		if receiver.chain.CurrentFastBlock().Hash() != newHead.Hash() || rawdb.ReadHeadFastBlockHash(receiver.db) != newHead.Hash() {
			t.Fatal("receipt path did not advance to the incompatible fast head")
		}
		t.Log("receipt insertion advanced the fast head using headers stored before checkpoint installation")
	case "checkpoint_commit_head":
		_, err := receiver.chain.InsertChain(later[:1])
		requireNoError(t, err)
		setSyntheticCheckpoint(anchor)
		requireNoError(t, receiver.chain.FastSyncCommitHead(later[0].Hash()))
		if receiver.chain.CurrentBlock().Hash() != later[0].Hash() || rawdb.ReadHeadBlockHash(receiver.db) != oldHead.Hash() {
			t.Fatal("fast commit did not reproduce its separate in-memory head change")
		}
		t.Log("fast-sync commit accepted incompatible stored state without checkpoint validation; the persisted full-head marker remained different")
	case "checkpoint_startup", "checkpoint_late_init":
		_, err := receiver.chain.InsertChain(later)
		requireNoError(t, err)
		receiver.chain.Stop()
		setSyntheticCheckpoint(anchor)
		if mode == "checkpoint_late_init" {
			datong.CheckPoints, datong.LastCheckPoint = nil, 0
		}
		receiver.engine = datong.New(receiver.chain.Config().DaTong, receiver.db)
		receiver.chain, err = core.NewBlockChain(receiver.db, &core.CacheConfig{TrieDirtyDisabled: true}, receiver.chain.Config(), receiver.engine, vm.Config{}, nil)
		requireNoError(t, err)
		if mode == "checkpoint_late_init" {
			setSyntheticCheckpoint(anchor)
			requireCanonicalTip(t, receiver, newHead)
			t.Log("loading checkpoint settings after chain construction left the incompatible head active without revalidation")
			return
		}
		requireCanonicalTip(t, receiver, shared)
		if rawdb.ReadCanonicalHash(receiver.db, anchor.NumberU64()) != (common.Hash{}) {
			t.Fatal("startup did not remove canonical data above the rewind")
		}
		t.Log("startup returned success after automatically rewinding an incompatible database below the checkpoint")
	case "checkpoint_body_shortcut":
		txs := types.Transactions{accepted[0].Transactions()[0], accepted[0].Transactions()[0]}
		header := accepted[0].Header()
		header.TxHash = types.DeriveSha(txs, trie.NewStackTrie(nil))
		block := types.NewBlockWithHeader(header).WithBody(txs, nil)
		requireErrorContains(t, receiver.chain.Validator().ValidateBody(block), "buying more than one ticket")
		setSyntheticCheckpoint(oldHead)
		requireNoError(t, receiver.chain.Validator().ValidateBody(block))
		t.Log("adding a later checkpoint disabled duplicate-ticket raw-body validation below it; this is a body-validator test, not a complete invalid-block import")
	default:
		t.Fatalf("unknown anchor path %q", mode)
	}
}

func buildAnchorBranch(t *testing.T, f *fixture, count int, spacing uint64) types.Blocks {
	t.Helper()
	blocks := make(types.Blocks, 0, count)
	for i := 0; i < count; i++ {
		parent := f.chain.CurrentBlock()
		tx := f.signPurchase(t, parent.Time(), common.TimeLockForever)
		block := f.buildBlockWithTransactions(t, parent.Time()+spacing, []*types.Transaction{tx})
		f.importBlock(t, block)
		blocks = append(blocks, block)
	}
	return blocks
}

func roundTripBlocks(t *testing.T, blocks types.Blocks) types.Blocks {
	t.Helper()
	encoded, err := rlp.EncodeToBytes(blocks)
	requireNoError(t, err)
	var received types.Blocks
	requireNoError(t, rlp.DecodeBytes(encoded, &received))
	return received
}

func blockHeaders(blocks types.Blocks) []*types.Header {
	headers := make([]*types.Header, len(blocks))
	for i, block := range blocks {
		headers[i] = block.Header()
	}
	return headers
}

func setSyntheticCheckpoint(block *types.Block) {
	points := make(map[uint64]common.Hash, len(datong.CheckPoints)+1)
	for height, hash := range datong.CheckPoints {
		points[height] = hash
	}
	points[block.NumberU64()] = block.Hash()
	datong.CheckPoints, datong.LastCheckPoint = points, block.NumberU64()
}

func requireCanonicalTip(t *testing.T, f *fixture, block *types.Block) {
	t.Helper()
	if f.chain.CurrentBlock().Hash() != block.Hash() || rawdb.ReadHeadBlockHash(f.db) != block.Hash() {
		t.Fatalf("unexpected full head: have=%s want=%s", f.chain.CurrentBlock().Hash().Hex(), block.Hash().Hex())
	}
}

func requireLinkedAncestor(t *testing.T, f *fixture, head, ancestor *types.Block) {
	t.Helper()
	header := head.Header()
	for header.Number.Uint64() > ancestor.NumberU64() {
		header = f.chain.GetHeader(header.ParentHash, header.Number.Uint64()-1)
		if header == nil {
			t.Fatal("missing ancestor header")
		}
	}
	if header.Hash() != ancestor.Hash() {
		t.Fatal("head did not follow the expected linked ancestry")
	}
}
