package restart

import (
	"bytes"
	"encoding/binary"
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func prepareReorgCost(t *testing.T, path string, depth int, shape string) {
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	f := newFixtureInDatabase(t, 0, db)
	f.chain.Stop()
	count, weight := depth+1, int64(1)
	if shape == "shorter" {
		count, weight = depth/2, 3
	}
	old := storeReorgCostBranch(t, db, f.parent.Header(), depth, 1, 1, true)
	winner := storeReorgCostBranch(t, db, f.parent.Header(), count, weight, 2, false)
	rawdb.WriteHeadBlockHash(db, old.Hash())
	rawdb.WriteHeadHeaderHash(db, old.Hash())
	rawdb.WriteHeadFastBlockHash(db, old.Hash())
	manifest := reorgCostManifest{Anchor: f.parent.Header(), OldTip: old.Hash(), NewTip: winner.Hash(), OldCount: depth, NewCount: count}
	requireNoError(t, writeStateExportJSON(filepath.Join(path, "manifest.json"), manifest))
	requireNoError(t, db.Close())
	var size int64
	requireNoError(t, filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.Mode().IsRegular() {
			size += info.Size()
		}
		return nil
	}))
	if size > 512<<20 {
		t.Fatalf("fixture exceeds 512 MiB: %d", size)
	}
	t.Logf("stored-branch fixture old=%d new=%d transactionsPerBlock=32 sharedPerHeight=8 logsPerReceipt=1 transactionDataBytes=256 logDataBytes=64 diskBytes=%d; unsigned, unexecuted, reused state", depth, count, size)
}

func storeReorgCostBranch(t *testing.T, db ethdb.Database, anchor *types.Header, count int, weight int64, branch byte, canonical bool) *types.Block {
	t.Helper()
	parent := anchor
	td := big.NewInt(1)
	var tip *types.Block
	for height := 1; height <= count; height++ {
		header := types.CopyHeader(parent)
		header.ParentHash = parent.Hash()
		header.Number = new(big.Int).Add(parent.Number, common.Big1)
		header.Time += 15
		header.Difficulty = big.NewInt(weight)
		header.Extra = []byte{branch}
		header.GasUsed = 32 * 50000
		txs := make(types.Transactions, 32)
		receipts := make(types.Receipts, len(txs))
		for i := range txs {
			data := make([]byte, 256)
			binary.BigEndian.PutUint64(data[1:9], uint64(height))
			data[9] = byte(i)
			if i >= 8 {
				data[0] = branch
			}
			txs[i] = types.NewTransaction(uint64(height*32+i), common.HexToAddress("0x1234"), big.NewInt(1), 50000, big.NewInt(1), data)
			receipts[i] = &types.Receipt{Status: types.ReceiptStatusSuccessful, CumulativeGasUsed: uint64(i+1) * 50000, Logs: []*types.Log{{Address: common.HexToAddress("0x1234"), Topics: []common.Hash{common.BytesToHash(data[:10])}, Data: bytes.Repeat([]byte{branch}, 64)}}}
			receipts[i].Bloom = types.CreateBloom(types.Receipts{receipts[i]})
		}
		tip = types.NewBlock(header, txs, nil, receipts, trie.NewStackTrie(nil))
		batch := db.NewBatch()
		rawdb.WriteBlock(batch, tip)
		rawdb.WriteReceipts(batch, tip.Hash(), tip.NumberU64(), receipts)
		td.Add(td, big.NewInt(weight))
		rawdb.WriteTd(batch, tip.Hash(), tip.NumberU64(), td)
		if canonical {
			rawdb.WriteCanonicalHash(batch, tip.Hash(), tip.NumberU64())
			rawdb.WriteTxLookupEntriesByBlock(batch, tip)
		}
		requireNoError(t, batch.Write())
		parent = tip.Header()
	}
	return tip
}

func verifyReorgCost(t *testing.T, path string) {
	manifest := readReorgCostManifest(t, path)
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	defer db.Close()
	expected := manifest.NewTip
	if os.Getenv("FUSION_REORG_COST_PHASE") == "before" {
		expected = manifest.OldTip
	}
	for _, head := range []common.Hash{rawdb.ReadHeadBlockHash(db), rawdb.ReadHeadHeaderHash(db), rawdb.ReadHeadFastBlockHash(db)} {
		if head != expected {
			t.Fatal("persisted heads are not the expected complete branch")
		}
	}
	config := reorgCostConfig(db, manifest)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, datong.New(config.DaTong, db), vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	if chain.CurrentBlock().Hash() != expected || chain.CurrentHeader().Hash() != expected || chain.CurrentFastBlock().Hash() != expected {
		t.Fatal("cold startup changed the expected branch")
	}
	requireNoError(t, chain.CheckRestartReady())
	_, err = chain.State()
	requireNoError(t, err)
	old := readReorgCostBranch(t, db, manifest.Anchor, manifest.OldTip, manifest.OldCount)
	winner := readReorgCostBranch(t, db, manifest.Anchor, manifest.NewTip, manifest.NewCount)
	canonical := winner
	if expected == manifest.OldTip {
		canonical = old
	}
	requireReorgCostIndexes(t, db, manifest.Anchor, old, winner, canonical)
	t.Logf("fresh-process verification passed: old=%d new=%d expectedHead=%s; complete canonical suffix, transaction indexes, receipt commitments, state and anchor readiness", manifest.OldCount, manifest.NewCount, expected.Hex())
}

func readReorgCostBranch(t *testing.T, db ethdb.Database, anchor *types.Header, tip common.Hash, count int) types.Blocks {
	t.Helper()
	blocks := make(types.Blocks, count)
	for i := count - 1; i >= 0; i-- {
		block := rawdb.ReadBlock(db, tip, anchor.Number.Uint64()+uint64(i+1))
		if block == nil {
			t.Fatal("missing stored branch body")
		}
		blocks[i], tip = block, block.ParentHash()
	}
	if tip != anchor.Hash() {
		t.Fatal("stored branch does not share the fixed anchor")
	}
	return blocks
}

func requireReorgCostIndexes(t *testing.T, db ethdb.Database, anchor *types.Header, old, winner, canonical types.Blocks) {
	t.Helper()
	wanted := make(map[common.Hash]uint64, len(canonical)*32)
	for _, block := range canonical {
		if rawdb.ReadCanonicalHash(db, block.NumberU64()) != block.Hash() {
			t.Fatal("canonical suffix contains a partial replacement")
		}
		for _, tx := range block.Transactions() {
			wanted[tx.Hash()] = block.NumberU64()
		}
	}
	if rawdb.ReadCanonicalHash(db, anchor.Number.Uint64()) != anchor.Hash() {
		t.Fatal("reorganization displaced its fixed anchor")
	}
	max := len(old)
	if len(winner) > max {
		max = len(winner)
	}
	for i := len(canonical) + 1; i <= max+1; i++ {
		if rawdb.ReadCanonicalHash(db, anchor.Number.Uint64()+uint64(i)) != (common.Hash{}) {
			t.Fatal("obsolete canonical suffix remains above the head")
		}
	}
	for _, branch := range []types.Blocks{old, winner} {
		for _, block := range branch {
			receipts := rawdb.ReadReceipts(db, block.Hash(), block.NumberU64(), params.MainnetChainConfig)
			if len(receipts) != 32 || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() || types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || types.CreateBloom(receipts) != block.Bloom() {
				t.Fatal("stored body or receipt commitments differ")
			}
			for i, tx := range block.Transactions() {
				position := rawdb.ReadTxLookupEntry(db, tx.Hash())
				number, exists := wanted[tx.Hash()]
				if exists && (position == nil || *position != number) || !exists && position != nil {
					t.Fatal("orphaned or shared transaction has an incorrect canonical lookup")
				}
				if receipts[i].TxHash != tx.Hash() || receipts[i].BlockHash != block.Hash() || len(receipts[i].Logs) != 1 || receipts[i].Logs[0].Removed {
					t.Fatal("stored receipt identity or log was changed")
				}
			}
		}
	}
	for _, block := range canonical {
		for _, i := range []int{0, 31} {
			tx := block.Transactions()[i]
			found, hash, height, index := rawdb.ReadTransaction(db, tx.Hash())
			receipt, receiptHash, receiptHeight, receiptIndex := rawdb.ReadReceipt(db, tx.Hash(), params.MainnetChainConfig)
			if found == nil || found.Hash() != tx.Hash() || hash != block.Hash() || height != block.NumberU64() || index != uint64(i) || receipt == nil || receiptHash != hash || receiptHeight != height || receiptIndex != index {
				t.Fatal("canonical shared or branch-specific transaction/receipt cannot be resolved")
			}
		}
	}
}
