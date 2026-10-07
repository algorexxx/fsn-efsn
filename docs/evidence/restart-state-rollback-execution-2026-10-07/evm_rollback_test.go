package state_test

import (
	"encoding/hex"
	"encoding/json"
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/vm"
)

type f11Observation[T any] struct {
	Available bool
	Panicked  bool
	Value     T
}

type f11ExecutionObservation struct {
	Output             string
	Error              string
	GasLeft            uint64
	Refund             uint64
	Deleted            bool
	Balances           f11Observation[map[common.Hash]string]
	TimeLock           f11Observation[*common.TimeLock]
	BeneficiaryBalance f11Observation[string]
	BeneficiaryLock    f11Observation[*common.TimeLock]
	OtherBalance       f11Observation[string]
	OtherLock          f11Observation[*common.TimeLock]
	Code               f11Observation[string]
	Storage            f11Observation[common.Hash]
	Nonce              f11Observation[uint64]
}

func TestF11ExecutionRollback(t *testing.T) {
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
		for _, london := range []bool{false, true} {
			era := "berlin"
			if london {
				era = "london"
			}
			for _, tc := range []struct {
				name      string
				asset     common.Hash
				zeroEntry bool
				revert    bool
			}{
				{"success_other", common.Hash{2}, false, false},
				{"revert_absent", common.Hash{2}, false, true},
				{"revert_zero", common.Hash{2}, true, true},
				{"revert_system", common.SystemAssetID, false, true},
				{"success_system", common.SystemAssetID, false, false},
			} {
				t.Run(mode.name+"/"+era+"/"+tc.name, func(t *testing.T) {
					child, parent, caller, beneficiary, other := common.Address{2}, common.Address{3}, common.Address{4}, common.Address{5}, common.Address{7}
					otherAsset := common.Hash{6}
					storageKey, storageValue := common.Hash{8}, common.Hash{9}
					db := rawdb.NewMemoryDatabase()
					defer db.Close()
					s, err := state.New(common.Hash{}, common.Hash{}, state.NewDatabase(db))
					if err != nil {
						t.Fatal(err)
					}
					childCode := append([]byte{byte(vm.PUSH20)}, beneficiary[:]...)
					childCode = append(childCode, byte(vm.SELFDESTRUCT))
					parentCode := []byte{byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH20)}
					parentCode = append(parentCode, child[:]...)
					parentCode = append(parentCode, byte(vm.PUSH3), 1, 0x86, 0xa0, byte(vm.CALL), byte(vm.PUSH1), 0, byte(vm.MSTORE), byte(vm.PUSH1), 32, byte(vm.PUSH1), 0)
					if tc.revert {
						parentCode = append(parentCode, byte(vm.REVERT))
					} else {
						parentCode = append(parentCode, byte(vm.RETURN))
					}
					s.SetCode(child, childCode)
					s.SetCode(parent, parentCode)
					s.SetNonce(child, 7)
					s.SetState(child, storageKey, storageValue)
					s.SetBalance(child, common.SystemAssetID, big.NewInt(11))
					s.SetBalance(child, otherAsset, big.NewInt(13))
					if tc.zeroEntry {
						s.SetBalance(child, tc.asset, big.NewInt(0))
					}
					s.SetTimeLockBalance(child, tc.asset, f11Lock(5))
					s.SetBalance(beneficiary, common.SystemAssetID, big.NewInt(3))
					s.SetTimeLockBalance(beneficiary, common.SystemAssetID, f11Lock(7))
					s.SetBalance(other, otherAsset, big.NewInt(17))
					s.SetTimeLockBalance(other, otherAsset, f11Lock(9))
					s.AddRefund(7)
					s.AddAddressToAccessList(child)
					s.AddAddressToAccessList(beneficiary)
					config := f11ExecutionConfig(mode.scheduled, london)
					evm := vm.NewEVM(vm.BlockContext{CanTransfer: core.CanTransfer, Transfer: core.Transfer, BlockNumber: big.NewInt(mode.height), Time: big.NewInt(2000000000), ParentTime: big.NewInt(1999999985), Difficulty: big.NewInt(1), BaseFee: big.NewInt(0), GasLimit: 1000000}, vm.TxContext{Origin: caller, GasPrice: big.NewInt(0)}, s, config, vm.Config{})
					wantBalances := map[common.Hash]string{}
					wantError, beneficiaryValue := "", "14"
					wantRefund := uint64(7)
					wantLock := new(common.TimeLock)
					beneficiaryLock := f11Lock(7)
					if tc.revert {
						wantError, beneficiaryValue = "execution reverted", "3"
						wantBalances = map[common.Hash]string{common.SystemAssetID: "11", otherAsset: "13"}
						wantLock = f11Lock(5)
					} else {
						if !london {
							wantRefund = 24007
						}
						if tc.asset == common.SystemAssetID {
							beneficiaryLock = f11Lock(12)
						}
					}
					want := f11ExecutionObservation{Output: "0000000000000000000000000000000000000000000000000000000000000001", Error: wantError, GasLeft: 194861, Refund: wantRefund, Deleted: !tc.revert, Balances: f11Observed(wantBalances), TimeLock: f11Observed(wantLock), BeneficiaryBalance: f11Observed(beneficiaryValue), BeneficiaryLock: f11Observed(beneficiaryLock), OtherBalance: f11Observed("17"), OtherLock: f11Observed(f11Lock(9)), Code: f11Observed(hex.EncodeToString(childCode)), Storage: f11Observed(storageValue), Nonce: f11Observed(uint64(7))}
					if tc.name == "revert_absent" && !mode.active {
						want.Balances = f11Observation[map[common.Hash]string]{Panicked: true}
					}

					output, gasLeft, callErr := evm.Call(vm.AccountRef(caller), parent, nil, 200000, big.NewInt(0))
					actual := f11ExecutionObservation{Output: hex.EncodeToString(output), GasLeft: gasLeft, Refund: s.GetRefund(), Deleted: s.HasSuicided(child), Balances: f11Read(func() map[common.Hash]string { return s.GetAllBalances(child) }), TimeLock: f11Read(func() *common.TimeLock { return s.GetTimeLockBalance(tc.asset, child) }), BeneficiaryBalance: f11Read(func() string { return s.GetBalance(common.SystemAssetID, beneficiary).String() }), BeneficiaryLock: f11Read(func() *common.TimeLock { return s.GetTimeLockBalance(common.SystemAssetID, beneficiary) }), OtherBalance: f11Read(func() string { return s.GetBalance(otherAsset, other).String() }), OtherLock: f11Read(func() *common.TimeLock { return s.GetTimeLockBalance(otherAsset, other) }), Code: f11Read(func() string { return hex.EncodeToString(s.GetCode(child)) }), Storage: f11Read(func() common.Hash { return s.GetState(child, storageKey) }), Nonce: f11Read(func() uint64 { return s.GetNonce(child) })}
					if callErr != nil {
						actual.Error = callErr.Error()
					}

					encoded, err := json.Marshal(actual)
					if err != nil {
						t.Fatal(err)
					}
					t.Logf("F11OBS %s %s", t.Name(), encoded)
					if !reflect.DeepEqual(actual, want) {
						t.Fatalf("observation differs: got=%+v want=%+v", actual, want)
					}
				})
			}
		}
	}
}

func f11Lock(value int64) *common.TimeLock {
	return &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 2000000001, EndTime: 2000000100, Value: big.NewInt(value)}}}
}

func f11Observed[T any](value T) f11Observation[T] {
	return f11Observation[T]{Available: true, Value: value}
}

func f11Read[T any](read func() T) (result f11Observation[T]) {
	defer func() {
		if recover() != nil {
			result.Panicked = true
		}
	}()
	result.Value = read()
	result.Available = true
	return result
}
