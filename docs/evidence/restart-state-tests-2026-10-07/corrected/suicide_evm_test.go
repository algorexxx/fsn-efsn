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

// TestSelfdestructParentRollback checks that when a parent call frame reverts,
// the child contract that executed SELFDESTRUCT is restored to the exact state
// it held before the call: no deletion flag, its original time-locked asset,
// and no spurious ordinary-balance entry.
//
// Corrected expectations versus the earlier probe:
//   - GetAllBalances omits zero ordinary balances by contract (CopyBalances
//     skips entries whose value Sign() == 0), so a restored child whose only
//     ordinary balance is the system asset at 0 must read back as an empty map,
//     not {SystemAssetID: "0"}.
//   - The restored child must still hold its original time lock.
//
// The restored-state reads are guarded with recover so an invalid-state panic
// is recorded as a failure of this subtest rather than crashing the binary and
// preventing the remaining subtests (including the successful control) from
// completing.
func TestSelfdestructParentRollback(t *testing.T) {
	wantReturn := common.FromHex("0000000000000000000000000000000000000000000000000000000000000001")
	wantTimeLock := &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(5)}}}
	wantBalances := map[common.Hash]string{}

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

			if !bytes.Equal(output, wantReturn) {
				t.Errorf("child CALL success result = %x, want %x", output, wantReturn)
			}

			if !test.revert {
				if callErr != nil || !statedb.HasSuicided(child) {
					t.Errorf("successful parent control: error=%v deleted=%v, want error=<nil> deleted=true", callErr, statedb.HasSuicided(child))
				}
				return
			}

			if callErr != vm.ErrExecutionReverted || statedb.HasSuicided(child) {
				t.Errorf("parent rollback: error=%v deleted=%v, want error=%v deleted=false", callErr, statedb.HasSuicided(child), vm.ErrExecutionReverted)
			}

			balances, timeLock := readRestoredChildState(t, statedb, child, test.asset)
			if !reflect.DeepEqual(balances, wantBalances) {
				t.Errorf("ordinary balances after parent rollback = %v, want %v", balances, wantBalances)
			}
			if !reflect.DeepEqual(timeLock, wantTimeLock) {
				t.Errorf("time lock after parent rollback = %v, want %v", timeLock, wantTimeLock)
			}
		})
	}
}

func readRestoredChildState(t *testing.T, statedb *state.StateDB, child common.Address, asset common.Hash) (balances map[common.Hash]string, timeLock *common.TimeLock) {
	t.Helper()
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("reading restored child state panicked; snapshot rollback left invalid account state: %v", r)
			balances = nil
			timeLock = nil
		}
	}()
	balances = statedb.GetAllBalances(child)
	timeLock = statedb.GetTimeLockBalance(asset, child)
	return
}
