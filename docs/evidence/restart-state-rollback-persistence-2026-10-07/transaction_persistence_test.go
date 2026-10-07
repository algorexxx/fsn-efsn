package state_test

import (
	"encoding/hex"
	"encoding/json"
	"math/big"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
)

type f11ReceiptObservation struct {
	Status     uint64
	Gas        uint64
	Cumulative uint64
	Index      uint
}

type f11PersistenceObservation struct {
	AfterTransaction state.F11AccountObservation
	Dirty            state.F11DirtyObservation
	Reopened         state.F11AccountObservation
	Receipts         []f11ReceiptObservation
	Sender           string
	SenderNonce      uint64
	Beneficiary      string
	Fees             string
}

func TestF11TransactionPersistence(t *testing.T) {
	for _, mode := range []struct {
		name      string
		height    int64
		scheduled bool
		active    bool
	}{
		{"disabled", 15130081, false, false},
		{"before", 15130080, true, false},
		{"at", 15130081, true, f11Candidate},
		{"after", 15130082, true, f11Candidate},
	} {
		for _, tc := range []struct {
			name             string
			priorTransaction bool
			zeroEntry        bool
			revert           bool
		}{
			{"clean_revert_absent", false, false, true},
			{"dirty_revert_absent", true, false, true},
			{"dirty_revert_zero", true, true, true},
			{"dirty_success_absent", true, false, false},
		} {
			t.Run(mode.name+"/"+tc.name, func(t *testing.T) {
				path := filepath.Join(t.TempDir(), "chain")
				db := f11Open(t, path, false)
				config := f11ExecutionConfig(mode.scheduled, true)
				keyBytes := make([]byte, 32)
				keyBytes[31] = 2
				key, err := crypto.ToECDSA(keyBytes)
				f11Require(t, err)
				sender := crypto.PubkeyToAddress(key.PublicKey)
				child, parent, beneficiary, miner := common.Address{2}, common.Address{3}, common.Address{5}, common.Address{6}
				asset := common.Hash{2}
				childCode := []byte{byte(vm.CALLDATASIZE), byte(vm.ISZERO), byte(vm.PUSH1), 6, byte(vm.JUMPI), byte(vm.STOP), byte(vm.JUMPDEST), byte(vm.PUSH20)}
				childCode = append(childCode, beneficiary[:]...)
				childCode = append(childCode, byte(vm.SELFDESTRUCT))
				parentCode := []byte{byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH20)}
				parentCode = append(parentCode, child[:]...)
				parentCode = append(parentCode, byte(vm.PUSH3), 1, 0x86, 0xa0, byte(vm.CALL), byte(vm.PUSH1), 0, byte(vm.MSTORE), byte(vm.PUSH1), 32, byte(vm.PUSH1), 0)
				if tc.revert {
					parentCode = append(parentCode, byte(vm.REVERT))
				} else {
					parentCode = append(parentCode, byte(vm.RETURN))
				}
				genesis := &core.Genesis{Config: config, GasLimit: 1000000, Difficulty: big.NewInt(1), Timestamp: 1999999985}
				genesisBlock, err := genesis.Commit(db)
				f11Require(t, err)
				cache := state.NewDatabase(db)
				seed, err := state.New(genesisBlock.Root(), common.Hash{}, cache)
				f11Require(t, err)
				seed.SetCode(child, childCode)
				seed.SetCode(parent, parentCode)
				seed.SetNonce(child, 7)
				seed.SetState(child, common.Hash{8}, common.Hash{9})
				seed.SetBalance(sender, common.SystemAssetID, big.NewInt(1000000))
				seed.SetBalance(child, common.SystemAssetID, big.NewInt(11))
				seed.SetBalance(beneficiary, common.SystemAssetID, big.NewInt(3))
				if tc.zeroEntry {
					seed.SetBalance(child, asset, big.NewInt(0))
				}
				seed.SetTimeLockBalance(child, asset, f11PersistenceLock())
				seed.SetTimeLockBalance(child, common.SystemAssetID, new(common.TimeLock))
				seedRoot, err := seed.Commit(true)
				f11Require(t, err)
				f11Require(t, cache.TrieDB().Commit(seedRoot, false, nil))
				previous := &types.Header{Number: big.NewInt(mode.height - 1), ParentHash: genesisBlock.Hash(), Root: seedRoot, Time: 1999999985, GasLimit: 1000000, Difficulty: big.NewInt(1), BaseFee: big.NewInt(0)}
				block := types.NewBlockWithHeader(previous)
				rawdb.WriteBlock(db, block)
				rawdb.WriteCanonicalHash(db, block.Hash(), block.NumberU64())
				rawdb.WriteHeadBlockHash(db, block.Hash())
				rawdb.WriteHeadHeaderHash(db, block.Hash())
				rawdb.WriteHeadFastBlockHash(db, block.Hash())
				chain, err := recovery.NewReader(db)
				f11Require(t, err)
				working, err := state.New(seedRoot, common.Hash{}, state.NewDatabase(db))
				f11Require(t, err)
				header := &types.Header{Number: big.NewInt(mode.height), ParentHash: block.Hash(), Time: 2000000000, GasLimit: 1000000, Difficulty: big.NewInt(1), BaseFee: big.NewInt(0), Coinbase: miner}
				var txs types.Transactions
				if tc.priorTransaction {
					tx, err := types.SignTx(types.NewTransaction(0, child, big.NewInt(1), 100000, big.NewInt(1), []byte{1}), types.NewEIP155Signer(config.ChainID), key)
					f11Require(t, err)
					txs = append(txs, tx)
				}
				tx, err := types.SignTx(types.NewTransaction(uint64(len(txs)), parent, big.NewInt(0), 100000, big.NewInt(1), nil), types.NewEIP155Signer(config.ChainID), key)
				f11Require(t, err)
				txs = append(txs, tx)
				childBalance, senderBalance, fees := "11", "968742", "31258"
				wantReceipts := []f11ReceiptObservation{{Status: 0, Gas: 31258, Cumulative: 31258, Index: 0}}
				if tc.priorTransaction {
					childBalance, senderBalance, fees = "12", "947707", "52292"
					wantReceipts = []f11ReceiptObservation{{Status: 1, Gas: 21034, Cumulative: 21034, Index: 0}, {Status: 0, Gas: 31258, Cumulative: 52292, Index: 1}}
				}
				wantChild := state.F11AccountObservation{Exists: true, BalanceIDs: []common.Hash{common.SystemAssetID}, Balances: []string{childBalance}, TimeLockIDs: []common.Hash{asset, common.SystemAssetID}, TimeLocks: []*common.TimeLock{f11PersistenceLock(), new(common.TimeLock)}, Nonce: 7, Code: hex.EncodeToString(childCode), Storage: common.Hash{9}}
				if tc.zeroEntry {
					wantChild.BalanceIDs = append(wantChild.BalanceIDs, asset)
					wantChild.Balances = append(wantChild.Balances, "0")
				}
				want := f11PersistenceObservation{AfterTransaction: wantChild, Reopened: wantChild, Dirty: state.F11DirtyObservation{Pending: tc.priorTransaction, Dirty: tc.priorTransaction}, Receipts: wantReceipts, Sender: senderBalance, SenderNonce: uint64(len(txs)), Beneficiary: "3", Fees: fees}
				if tc.revert && !tc.zeroEntry && !mode.active {
					want.AfterTransaction.BalanceIDs = append(append([]common.Hash{}, wantChild.BalanceIDs...), asset)
					want.AfterTransaction.Balances = append(append([]string{}, wantChild.Balances...), "<nil>")
					if tc.priorTransaction {
						want.Reopened.BalanceIDs = append(append([]common.Hash{}, wantChild.BalanceIDs...), asset)
						want.Reopened.Balances = append(append([]string{}, wantChild.Balances...), "0")
					}
				}
				if !tc.revert {
					want.AfterTransaction, want.Reopened = state.F11AccountObservation{}, state.F11AccountObservation{}
					want.Beneficiary = "15"
					want.Receipts[len(want.Receipts)-1].Status = 1
				}

				actual := f11PersistenceObservation{}
				gasPool := new(core.GasPool).AddGas(header.GasLimit)
				for index, tx := range txs {
					working.Prepare(tx.Hash(), index)
					receipt, err := core.ApplyTransaction(config, chain, &miner, gasPool, working, header, tx, &header.GasUsed, vm.Config{})
					f11Require(t, err)
					if receipt.TxHash != tx.Hash() || len(receipt.Logs) != 0 || len(receipt.PostState) != 0 || receipt.Bloom != (types.Bloom{}) {
						t.Fatal("unexpected receipt identity, logs, state or bloom")
					}
					actual.Receipts = append(actual.Receipts, f11ReceiptObservation{Status: receipt.Status, Gas: receipt.GasUsed, Cumulative: receipt.CumulativeGasUsed, Index: receipt.TransactionIndex})
				}
				actual.AfterTransaction = state.F11InspectAccount(working, child)
				actual.Dirty = state.F11InspectDirty(working, child)
				root, err := working.Commit(true)
				f11Require(t, err)
				f11Require(t, working.Database().TrieDB().Commit(root, false, nil))
				f11Require(t, db.Close())
				db = f11Open(t, path, true)
				defer db.Close()
				reopened, err := state.New(root, common.Hash{}, state.NewDatabase(db))
				f11Require(t, err)
				actual.Reopened = state.F11InspectAccount(reopened, child)
				actual.Sender = reopened.GetBalance(common.SystemAssetID, sender).String()
				actual.SenderNonce = reopened.GetNonce(sender)
				actual.Beneficiary = reopened.GetBalance(common.SystemAssetID, beneficiary).String()
				actual.Fees = reopened.GetBalance(common.SystemAssetID, miner).String()

				encoded, err := json.Marshal(actual)
				f11Require(t, err)
				t.Logf("F11PERSIST %s %s", t.Name(), encoded)
				t.Logf("F11ROOT %s %s", t.Name(), root.Hex())
				if !reflect.DeepEqual(actual, want) {
					expected, _ := json.Marshal(want)
					t.Fatalf("state/receipt mismatch: got=%s want=%s", encoded, expected)
				}
				if header.GasUsed != want.Receipts[len(want.Receipts)-1].Cumulative {
					t.Fatal("header gas differs from expected cumulative gas")
				}
			})
		}
	}
}

func f11PersistenceLock() *common.TimeLock {
	return &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(5)}}}
}

func f11Open(t *testing.T, path string, readonly bool) ethdb.Database {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "f11-persistence", readonly)
	f11Require(t, err)
	t.Cleanup(func() { db.Close() })
	return db
}

func f11Require(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}
