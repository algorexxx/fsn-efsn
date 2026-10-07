package state

import (
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
)

func TestSuicideSnapshotRestoresFlag(t *testing.T) {
	for _, test := range []struct {
		name        string
		readBalance bool
	}{
		{name: "no_balance_entries"},
		{name: "system_balance_read_before_snapshot", readBalance: true},
	} {
		t.Run(test.name, func(t *testing.T) {
			address := common.Address{1}
			statedb, err := New(common.Hash{}, common.Hash{}, NewDatabase(rawdb.NewMemoryDatabase()))
			if err != nil {
				t.Fatal(err)
			}
			statedb.SetNonce(address, 1)
			if test.readBalance {
				statedb.GetBalance(common.SystemAssetID, address)
			}
			snapshot := statedb.Snapshot()

			deleted := statedb.Suicide(address)
			statedb.RevertToSnapshot(snapshot)

			if !deleted {
				t.Fatal("existing fixture account was not marked for deletion")
			}
			if statedb.HasSuicided(address) {
				t.Error("snapshot rollback retained the account deletion flag")
			}
		})
	}
}

func TestSuicideSnapshotPreservesTimeLockAsset(t *testing.T) {
	address := common.Address{1}
	asset := common.Hash{2}
	wantAssetIDs := []common.Hash{common.SystemAssetID}
	wantBalances := []*big.Int{big.NewInt(0)}
	wantTimeLockIDs := []common.Hash{asset}
	wantTimeLocks := []*common.TimeLock{{Items: []*common.TimeLockItem{{StartTime: 100, EndTime: 200, Value: big.NewInt(5)}}}}
	statedb, err := New(common.Hash{}, common.Hash{}, NewDatabase(rawdb.NewMemoryDatabase()))
	if err != nil {
		t.Fatal(err)
	}
	statedb.SetNonce(address, 1)
	statedb.GetBalance(common.SystemAssetID, address)
	statedb.SetTimeLockBalance(address, asset, &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 100, EndTime: 200, Value: big.NewInt(5)}}})
	snapshot := statedb.Snapshot()

	deleted := statedb.Suicide(address)
	statedb.RevertToSnapshot(snapshot)
	account := statedb.getStateObject(address).data

	if !deleted || statedb.HasSuicided(address) {
		t.Error("account deletion flag did not complete a mark-and-revert cycle")
	}
	if !reflect.DeepEqual(account.BalancesHash, wantAssetIDs) || !reflect.DeepEqual(account.BalancesVal, wantBalances) {
		t.Errorf("ordinary balances changed across snapshot rollback: IDs=%v values=%v", account.BalancesHash, account.BalancesVal)
	}
	if !reflect.DeepEqual(account.TimeLockBalancesHash, wantTimeLockIDs) || !reflect.DeepEqual(account.TimeLockBalancesVal, wantTimeLocks) {
		t.Errorf("time-lock balances changed across snapshot rollback: IDs=%v values=%v", account.TimeLockBalancesHash, account.TimeLockBalancesVal)
	}
}
