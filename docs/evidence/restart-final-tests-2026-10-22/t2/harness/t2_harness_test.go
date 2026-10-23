package restart

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"math/big"
	"os"
	"path/filepath"
	"strconv"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type t2HistoryIdentity struct {
	Head       *types.Header
	Previous   *types.Header
	PreviousTD *big.Int
	HeadTD     *big.Int
}

type t2HistoryResult struct {
	First        uint64
	Last         uint64
	Blocks       uint64
	Transactions uint64
	Bytes        uint64
	SHA256       string
}

// TestT2PrepareNode turns one verified copy of the compact export into a T2 node
// seed: the audited key-1/key-2 substitutions, then (optionally) the genuine
// 90,000-block ancestry segment. The node directory is <datadir>/efsn.
func TestT2PrepareNode(t *testing.T) {
	directory := os.Getenv("T2_NODE_FIXTURE")
	if directory == "" {
		t.Skip("set T2_NODE_FIXTURE to a verified disposable compact-export copy")
	}
	if !filepath.IsAbs(directory) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable path and no backup source environment required")
	}
	requireFullStateCopy(t, directory)
	prepareFullStateHandover(t, directory)
	f, original, funding := openFullStateHandover(t, directory)
	if history := os.Getenv("T2_HISTORY_INPUT"); history != "" {
		installT2History(t, f, original, directory, history)
	}
	head := f.chain.CurrentBlock()
	if head.Hash() != funding.Parent.Hash() {
		t.Fatal("seed head is not the audited synthetic parent")
	}
	t.Logf("T2-SEED parent=%s number=%d root=%s tickets=%s", head.Hash().Hex(), head.NumberU64(), head.Root().Hex(), head.MixDigest().Hex())
}

// TestT2RivalChain extends a prepared seed with a rival pre-restart chain: the same
// key-1/key-2 recovery shape as the canonical blocks but with different
// timestamps, followed by T2_RIVAL_BLOCKS ordinary key-2 blocks with purchases.
func TestT2RivalChain(t *testing.T) {
	directory := os.Getenv("T2_RIVAL_FIXTURE")
	if directory == "" {
		t.Skip("set T2_RIVAL_FIXTURE to a prepared T2 seed")
	}
	count, err := strconv.Atoi(os.Getenv("T2_RIVAL_BLOCKS"))
	requireNoError(t, err)
	original, _, funding := openFullStateHandover(t, directory)
	successor := *original
	selectHandoverSuccessor(t, &successor, funding)
	var blocks types.Blocks
	for i := 0; i < 3+count; i++ {
		parent := original.chain.CurrentBlock()
		signer, timestamp := &successor, jumpTime+600+uint64(i-1)*120
		if i == 0 {
			signer, timestamp = original, parent.Time()+180
		}
		end := ticketEnd
		if end < parent.Time()+31*24*3600 {
			end = parent.Time() + 31*24*3600
		}
		tx := successor.signPurchase(t, parent.Time(), end)
		block := signer.buildBlockWithTransactions(t, timestamp, []*types.Transaction{tx})
		original.importBlock(t, block)
		blocks = append(blocks, block)
	}
	encoded, err := rlp.EncodeToBytes(blocks)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(directory, "rival-blocks.rlp"), encoded, 0600))
	head := original.chain.CurrentBlock()
	t.Logf("T2-RIVAL first=%s head=%d hash=%s td=%s", blocks[0].Hash().Hex(), head.NumberU64(), head.Hash().Hex(), original.chain.GetTd(head.Hash(), head.NumberU64()))
}

func installT2History(t *testing.T, f *fixture, original fullStateFixtureLedger, directory, path string) {
	t.Helper()
	if !filepath.IsAbs(path) {
		t.Fatal("absolute history segment required")
	}
	verified := readT2History(t, path, nil)
	var exported t2HistoryResult
	readHandoverJSON(t, path+".export.json", &exported)
	if verified != exported {
		t.Fatal("history bytes differ from verified export")
	}
	head := f.chain.CurrentBlock().Hash()
	batch := f.db.NewBatch()
	count := 0
	actual := readT2History(t, path, func(block *types.Block, td *big.Int) {
		if block.NumberU64() == original.Source.Number.Uint64() {
			if block.Hash() != original.Source.Hash() || block.ParentHash() != original.Parent.ParentHash {
				t.Fatal("history does not attach to audited synthetic parent")
			}
			return
		}
		stored := rawdb.ReadCanonicalHash(f.db, block.NumberU64())
		if stored != (common.Hash{}) && stored != block.Hash() {
			t.Fatal("history conflicts with an existing canonical header")
		}
		rawdb.WriteBlock(batch, block)
		rawdb.WriteTd(batch, block.Hash(), block.NumberU64(), td)
		rawdb.WriteCanonicalHash(batch, block.Hash(), block.NumberU64())
		count++
		if count%1000 == 0 {
			requireNoError(t, batch.Write())
			batch.Reset()
		}
	})
	requireNoError(t, batch.Write())
	if actual != verified || count != params.FullImmutabilityThreshold || f.chain.CurrentBlock().Hash() != head || rawdb.ReadHeadBlockHash(f.db) != head || rawdb.ReadHeadHeaderHash(f.db) != head || rawdb.ReadHeadFastBlockHash(f.db) != head {
		t.Fatal("history install changed the active head or source identity")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(directory, "history-installed.json"), verified))
	t.Logf("genuine ancestry installed blocks=%d from=%d through=%d sha256=%s; synthetic parent and heads unchanged", count, verified.First, verified.Last-1, verified.SHA256)
}

func readT2History(t *testing.T, path string, visit func(*types.Block, *big.Int)) t2HistoryResult {
	t.Helper()
	file, err := os.Open(path)
	requireNoError(t, err)
	defer file.Close()
	hash := sha256.New()
	stream := rlp.NewStream(io.TeeReader(file, hash), 0)
	var identity t2HistoryIdentity
	requireNoError(t, stream.Decode(&identity))
	var context fullStateContext
	data, err := os.ReadFile("testdata/context.rlp")
	requireNoError(t, err)
	requireNoError(t, rlp.DecodeBytes(data, &context))
	if identity.Head == nil || identity.Previous == nil || identity.PreviousTD == nil || identity.HeadTD == nil || identity.PreviousTD.Sign() <= 0 || identity.Head.Hash() != context.Parent.Hash() || identity.HeadTD.Cmp(context.TotalDifficulty) != 0 || identity.Previous.Number.Uint64()+params.FullImmutabilityThreshold+1 != identity.Head.Number.Uint64() {
		t.Fatal("history identity does not match trusted preserved context")
	}
	result := t2HistoryResult{First: identity.Previous.Number.Uint64() + 1, Last: identity.Head.Number.Uint64()}
	previous, td := identity.Previous, new(big.Int).Set(identity.PreviousTD)
	for number := result.First; number <= result.Last; number++ {
		var block *types.Block
		requireNoError(t, stream.Decode(&block))
		requireNoError(t, checkT2HistoryBlock(block, previous))
		td.Add(td, block.Difficulty())
		if visit != nil {
			visit(block, new(big.Int).Set(td))
		}
		result.Blocks++
		result.Transactions += uint64(len(block.Transactions()))
		previous = block.Header()
	}
	var extra types.Block
	if err := stream.Decode(&extra); err != io.EOF || previous.Hash() != identity.Head.Hash() || td.Cmp(identity.HeadTD) != 0 {
		t.Fatal("history ends incorrectly or has trailing data")
	}
	stat, err := file.Stat()
	requireNoError(t, err)
	result.Bytes, result.SHA256 = uint64(stat.Size()), hex.EncodeToString(hash.Sum(nil))
	return result
}

func checkT2HistoryBlock(block *types.Block, previous *types.Header) error {
	if block == nil || previous == nil || block.NumberU64() != previous.Number.Uint64()+1 || block.ParentHash() != previous.Hash() || block.Difficulty().Sign() <= 0 {
		return fmt.Errorf("missing or discontinuous historical block")
	}
	if types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || len(block.Uncles()) != 0 {
		return fmt.Errorf("historical block body commitment mismatch at %d", block.NumberU64())
	}
	return nil
}
