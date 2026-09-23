package restart

import (
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func TestStateIntegrityDetectsMissingAndCorruptData(t *testing.T) {
	for _, damage := range []string{"none", "account root", "storage root", "missing code", "corrupt code"} {
		t.Run(damage, func(t *testing.T) {
			db := rawdb.NewMemoryDatabase()
			t.Cleanup(func() { db.Close() })
			cache := state.NewDatabase(db)
			statedb, err := state.New(common.Hash{}, common.Hash{}, cache)
			requireNoError(t, err)
			owner := common.HexToAddress("0x1234")
			code := []byte{0x60, 0x01, 0x00}
			statedb.SetBalance(owner, common.SystemAssetID, big.NewInt(1))
			statedb.SetCode(owner, code)
			statedb.SetState(owner, common.HexToHash("0x01"), common.HexToHash("0x02"))
			root, err := statedb.Commit(false)
			requireNoError(t, err)
			requireNoError(t, cache.TrieDB().Commit(root, false, nil))
			switch damage {
			case "account root":
				rawdb.DeleteTrieNode(db, root)
			case "storage root":
				rawdb.DeleteTrieNode(db, statedb.StorageTrie(owner).Hash())
			case "missing code":
				rawdb.DeleteCode(db, crypto.Keccak256Hash(code))
			case "corrupt code":
				rawdb.WriteCode(db, crypto.Keccak256Hash(code), []byte{0xff})
			}
			result, err := inspectState(db, root, func(stateInspection) {})
			if damage != "none" {
				if err == nil {
					t.Fatal("inspection accepted deliberately damaged state")
				}
				return
			}
			requireNoError(t, err)
			if result != (stateInspection{Accounts: 1, StorageLeaves: 1, CodeReferences: 1, CodeBytes: 3}) {
				t.Fatalf("unexpected complete-state inventory: %+v", result)
			}
		})
	}
}

func TestHistoryIntegrityDetectsMissingAndCorruptData(t *testing.T) {
	for _, damage := range []string{"none", "body", "receipts", "difficulty", "transactions", "parent"} {
		t.Run(damage, func(t *testing.T) {
			db := rawdb.NewMemoryDatabase()
			t.Cleanup(func() { db.Close() })
			blocks := writeInspectionHistory(db)
			block := blocks[1]
			switch damage {
			case "body":
				rawdb.DeleteBody(db, block.Hash(), 1)
			case "receipts":
				rawdb.WriteReceipts(db, block.Hash(), 1, types.Receipts{{Status: 1, CumulativeGasUsed: 1}})
			case "difficulty":
				rawdb.WriteTd(db, block.Hash(), 1, big.NewInt(999))
			case "transactions":
				rawdb.WriteBody(db, block.Hash(), 1, &types.Body{})
			case "parent":
				header := block.Header()
				header.ParentHash = common.Hash{1}
				changed := types.NewBlockWithHeader(header).WithBody(block.Transactions(), nil)
				rawdb.WriteBlock(db, changed)
				rawdb.WriteCanonicalHash(db, changed.Hash(), 1)
			}
			result, err := inspectHistory(db, params.AllEthashProtocolChanges, 2, func(historyInspection) {})
			if damage != "none" {
				if err == nil {
					t.Fatal("inspection accepted deliberately damaged history")
				}
				return
			}
			requireNoError(t, err)
			if result.Blocks != 3 || result.Transactions != 2 || result.Receipts != 2 || result.LastHash != blocks[2].Hash() || result.TotalDifficulty.Cmp(big.NewInt(3)) != 0 {
				t.Fatalf("unexpected history inventory: %+v", result)
			}
		})
	}
}

func writeInspectionHistory(db ethdb.Database) []*types.Block {
	blocks := make([]*types.Block, 0, 3)
	var parent common.Hash
	for height := uint64(0); height < 3; height++ {
		var transactions []*types.Transaction
		var receipts types.Receipts
		if height != 0 {
			transactions = []*types.Transaction{types.NewTransaction(height, common.Address{1}, big.NewInt(1), 21000, big.NewInt(1), nil)}
			receipts = types.Receipts{{Status: 1, CumulativeGasUsed: 21000}}
		}
		header := &types.Header{ParentHash: parent, Number: new(big.Int).SetUint64(height), Difficulty: big.NewInt(1), GasLimit: 30000000}
		block := types.NewBlock(header, transactions, nil, receipts, trie.NewStackTrie(nil))
		rawdb.WriteBlock(db, block)
		rawdb.WriteCanonicalHash(db, block.Hash(), height)
		rawdb.WriteTd(db, block.Hash(), height, new(big.Int).SetUint64(height+1))
		rawdb.WriteReceipts(db, block.Hash(), height, receipts)
		blocks = append(blocks, block)
		parent = block.Hash()
	}
	return blocks
}
