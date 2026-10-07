package state_test

import (
	"bytes"
	"fmt"
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

// TestSelfdestructParentRollback checks what SELFDESTRUCT inside a reverting
// parent call frame leaves behind for the child contract.
//
// The isolating variable is NOT system versus non-system asset. It is whether
// an ordinary-balance entry already exists for the self-destructed asset when
// StateDB.Suicide runs. StateDB.Suicide's time-lock journal loop builds a
// suicideChange without isTimeLock:true, so on rollback suicideChange.revert
// takes the ordinary-balance branch and calls setBalance(asset, nil). If the
// asset already had an ordinary entry, the ordinary loop's own suicideChange
// reverts that entry back to its prior value and no nil survives. If it did
// not, the nil entry persists and later reads of it panic.
//
// A zero-valued ordinary entry and an absent ordinary entry are different
// structural states; only absence triggers the defect. These cases vary that
// precondition directly: the system asset is shown clean only because the EVM
// SELFDESTRUCT path (opSelfdestruct reads GetBalance(SystemAssetID) first, and
// this fixture also seeds it) guarantees it already has an ordinary entry.
//
// Observations of the restored child are taken per field, each guarded so a
// read that panics is recorded as an unavailable observation rather than
// crashing the binary or being mistaken for observed account contents.
//
// Scope of the restored-balance check: GetAllBalances -> CopyBalances omits
// entries whose value Sign()==0, so an empty-map result confirms only that no
// non-zero ordinary balance is present. It does not prove the raw account
// representation (BalancesHash/BalancesVal arrays) is identical to the
// original; that structural check lives in the direct-state fixture
// core/state/suicide_test.go (TestSuicideSnapshotPreservesTimeLockAsset).
func TestSelfdestructParentRollback(t *testing.T) {
	wantReturn := common.FromHex("0000000000000000000000000000000000000000000000000000000000000001")
	wantTimeLock := &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(5)}}}
	wantBalances := map[common.Hash]string{}

	for _, test := range []struct {
		name string
		// asset carries the child's time lock and is the SELFDESTRUCT asset.
		asset common.Hash
		// seedOrdinaryEntry seeds a zero-valued ordinary entry for asset before
		// the call, so the precondition (ordinary entry present) is satisfied.
		seedOrdinaryEntry bool
		revert            bool
		// expectBalanceReadUnavailable records the known defect: the restored
		// ordinary-balance read panics on a persisted nil entry.
		expectBalanceReadUnavailable bool
	}{
		{name: "successful_child_and_parent", asset: common.Hash{2}},
		{name: "reverted_asset_without_ordinary_entry", asset: common.Hash{2}, revert: true, expectBalanceReadUnavailable: true},
		{name: "reverted_asset_with_zero_ordinary_entry", asset: common.Hash{2}, seedOrdinaryEntry: true, revert: true},
		{name: "reverted_system_asset_with_ordinary_entry", asset: common.SystemAssetID, revert: true},
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
			if test.seedOrdinaryEntry {
				statedb.SetBalance(child, test.asset, big.NewInt(0))
			}
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

			// Each field is observed independently; a panic marks that field
			// unavailable and never substitutes a placeholder for the other.
			balances, balancesAvailable, balancesErr := observeBalances(statedb, child)
			timeLock, timeLockAvailable, timeLockErr := observeTimeLock(statedb, test.asset, child)

			switch {
			case !balancesAvailable && test.expectBalanceReadUnavailable:
				t.Errorf("restored ordinary-balance read unavailable: rollback left an invalid (nil) ordinary entry and GetAllBalances panicked: %s", balancesErr)
			case !balancesAvailable:
				t.Errorf("restored ordinary-balance read unexpectedly unavailable (panic): %s", balancesErr)
			case !reflect.DeepEqual(balances, wantBalances):
				t.Errorf("restored ordinary balances (zero entries omitted by CopyBalances) = %v, want %v", balances, wantBalances)
			}

			switch {
			case !timeLockAvailable:
				t.Errorf("restored time-lock read unavailable (panic), observation of this field not obtained: %s", timeLockErr)
			case !reflect.DeepEqual(timeLock, wantTimeLock):
				t.Errorf("restored time lock = %v, want %v", timeLock, wantTimeLock)
			default:
				t.Logf("restored time lock independently observed as unchanged: %v", timeLock)
			}
		})
	}
}

// observeBalances reads the restored ordinary balances, reporting availability
// separately from contents so a panic is not mistaken for an observed value.
func observeBalances(statedb *state.StateDB, addr common.Address) (balances map[common.Hash]string, available bool, failure string) {
	defer func() {
		if r := recover(); r != nil {
			balances = nil
			available = false
			failure = fmt.Sprintf("%v", r)
		}
	}()
	balances = statedb.GetAllBalances(addr)
	available = true
	return
}

// observeTimeLock reads the restored time lock for one asset, independently of
// the ordinary-balance read, with the same availability/contents separation.
func observeTimeLock(statedb *state.StateDB, asset common.Hash, addr common.Address) (timeLock *common.TimeLock, available bool, failure string) {
	defer func() {
		if r := recover(); r != nil {
			timeLock = nil
			available = false
			failure = fmt.Sprintf("%v", r)
		}
	}()
	timeLock = statedb.GetTimeLockBalance(asset, addr)
	available = true
	return
}
