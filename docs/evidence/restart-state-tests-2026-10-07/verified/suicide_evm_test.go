package state_test

import (
	"bytes"
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestSelfdestructParentRollback(t *testing.T) {
	for _, test := range []struct {
		name   string
		asset  common.Hash
		revert bool
	}{
		{name: "successful_child_and_parent", asset: common.Hash{2}},
		{name: "reverted_system_time_lock", asset: common.SystemAssetID, revert: true},
		{name: "reverted_other_asset_time_lock", asset: common.Hash{2}, revert: true},
	} {
		t.Run(test.name, func(t *testing.T) {
			child, parent, caller, beneficiary := common.Address{2}, common.Address{3}, common.Address{4}, common.Address{5}
			wantBalances := map[common.Hash]string{common.SystemAssetID: "0"}
			wantTimeLock := &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(5)}}}
			wantReturn := common.FromHex("0000000000000000000000000000000000000000000000000000000000000001")
			statedb, err := state.New(common.Hash{}, common.Hash{}, state.NewDatabase(rawdb.NewMemoryDatabase()))
			if err != nil {
				t.Fatal(err)
			}
			childCode := append([]byte{byte(vm.PUSH20)}, beneficiary[:]...)
			childCode = append(childCode, byte(vm.SELFDESTRUCT))
			parentCode := []byte{byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH20)}
			parentCode = append(parentCode, child[:]...)
			parentCode = append(parentCode, byte(vm.PUSH3), 1, 0x86, 0xa0, byte(vm.CALL), byte(vm.PUSH1), 0, byte(vm.MSTORE), byte(vm.PUSH1), 32, byte(vm.PUSH1), 0)
			if test.revert {
				parentCode = append(parentCode, byte(vm.REVERT))
			} else {
				parentCode = append(parentCode, byte(vm.RETURN))
			}
			statedb.SetCode(child, childCode)
			statedb.SetCode(parent, parentCode)
			statedb.SetBalance(child, common.SystemAssetID, big.NewInt(0))
			statedb.SetTimeLockBalance(child, test.asset, &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(5)}}})
			evm := vm.NewEVM(vm.BlockContext{
				CanTransfer: core.CanTransfer, Transfer: core.Transfer,
				BlockNumber: big.NewInt(15130081), Time: big.NewInt(2000000000), ParentTime: big.NewInt(1999999985),
				Difficulty: big.NewInt(1), BaseFee: big.NewInt(0), GasLimit: 1000000,
			}, vm.TxContext{Origin: caller, GasPrice: big.NewInt(0)}, statedb, params.MainnetChainConfig, vm.Config{})

			output, _, callErr := evm.Call(vm.AccountRef(caller), parent, nil, 200000, big.NewInt(0))
			balances := statedb.GetAllBalances(child)

			if !bytes.Equal(output, wantReturn) {
				t.Errorf("child CALL success result = %x, want %x", output, wantReturn)
			}
			if !test.revert {
				if callErr != nil || !statedb.HasSuicided(child) {
					t.Errorf("successful parent control: error=%v deleted=%v", callErr, statedb.HasSuicided(child))
				}
				return
			}
			if callErr != vm.ErrExecutionReverted || statedb.HasSuicided(child) {
				t.Errorf("parent rollback: error=%v deleted=%v", callErr, statedb.HasSuicided(child))
			}
			if !reflect.DeepEqual(balances, wantBalances) {
				t.Errorf("ordinary balances after parent rollback = %v, want %v", balances, wantBalances)
			}
			if got := statedb.GetTimeLockBalance(test.asset, child); !reflect.DeepEqual(got, wantTimeLock) {
				t.Errorf("time lock after parent rollback = %v, want %v", got, wantTimeLock)
			}
		})
	}
}
