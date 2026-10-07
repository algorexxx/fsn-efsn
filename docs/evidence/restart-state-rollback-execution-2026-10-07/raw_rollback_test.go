package state

import (
	"encoding/json"
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
)

type f11RawObservation struct {
	Deleted     bool
	BalanceIDs  []common.Hash
	Balances    []string
	TimeLockIDs []common.Hash
	TimeLocks   []*common.TimeLock
}

func TestF11RawRollback(t *testing.T) {
	for _, fix := range []bool{false, true} {
		mode := "disabled"
		if fix {
			mode = "enabled"
		}
		for _, entry := range []string{"absent", "zero", "nonzero"} {
			t.Run(mode+"/"+entry, func(t *testing.T) {
				address := common.Address{1}
				asset, unrelated := common.Hash{2}, common.Hash{3}
				db := rawdb.NewMemoryDatabase()
				defer db.Close()
				s, err := New(common.Hash{}, common.Hash{}, NewDatabase(db))
				if err != nil {
					t.Fatal(err)
				}
				s.SetBalance(address, common.SystemAssetID, big.NewInt(11))
				s.SetBalance(address, unrelated, big.NewInt(13))
				want := f11RawObservation{BalanceIDs: []common.Hash{common.SystemAssetID, unrelated}, Balances: []string{"11", "13"}, TimeLockIDs: []common.Hash{asset}, TimeLocks: []*common.TimeLock{{Items: []*common.TimeLockItem{{StartTime: 100, EndTime: 200, Value: big.NewInt(5)}}}}}
				if entry != "absent" {
					value := int64(0)
					text := "0"
					if entry == "nonzero" {
						value, text = 17, "17"
					}
					s.SetBalance(address, asset, big.NewInt(value))
					want.BalanceIDs = append(want.BalanceIDs, asset)
					want.Balances = append(want.Balances, text)
				}
				s.SetTimeLockBalance(address, asset, &common.TimeLock{Items: []*common.TimeLockItem{{StartTime: 100, EndTime: 200, Value: big.NewInt(5)}}})
				snapshot := s.Snapshot()
				if entry == "absent" && !(fix && f11RawCandidate) {
					want.BalanceIDs = append(want.BalanceIDs, asset)
					want.Balances = append(want.Balances, "<nil>")
				}

				marked := f11Delete(s, address, fix)
				s.RevertToSnapshot(snapshot)
				account := s.getStateObject(address).data
				actual := f11RawObservation{Deleted: s.HasSuicided(address), BalanceIDs: account.BalancesHash, TimeLockIDs: account.TimeLockBalancesHash, TimeLocks: account.TimeLockBalancesVal}
				for _, balance := range account.BalancesVal {
					value := "<nil>"
					if balance != nil {
						value = balance.String()
					}
					actual.Balances = append(actual.Balances, value)
				}

				encoded, err := json.Marshal(actual)
				if err != nil {
					t.Fatal(err)
				}
				t.Logf("F11OBS %s %s", t.Name(), encoded)
				if !marked || !reflect.DeepEqual(actual, want) {
					t.Fatalf("raw observation differs: marked=%v got=%+v want=%+v", marked, actual, want)
				}
			})
		}
	}
}

func TestF11EmptyEntryDefectUnchanged(t *testing.T) {
	for _, fix := range []bool{false, true} {
		mode := "disabled"
		if fix {
			mode = "enabled"
		}
		for _, readBalance := range []bool{false, true} {
			name := "absent"
			if readBalance {
				name = "ordinary_entry"
			}
			t.Run(mode+"/"+name, func(t *testing.T) {
				address := common.Address{1}
				db := rawdb.NewMemoryDatabase()
				defer db.Close()
				s, err := New(common.Hash{}, common.Hash{}, NewDatabase(db))
				if err != nil {
					t.Fatal(err)
				}
				s.SetNonce(address, 1)
				if readBalance {
					s.GetBalance(common.SystemAssetID, address)
				}
				snapshot := s.Snapshot()

				marked := f11Delete(s, address, fix)
				s.RevertToSnapshot(snapshot)
				actual := s.HasSuicided(address)

				t.Logf("F11OBS %s {\"Deleted\":%v}", t.Name(), actual)
				if !marked || actual != !readBalance {
					t.Fatalf("empty-entry legacy defect changed: marked=%v deleted=%v", marked, actual)
				}
			})
		}
	}
}
