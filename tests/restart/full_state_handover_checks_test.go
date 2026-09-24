package restart

import (
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestHandoverFundingGuard(t *testing.T) {
	for _, damage := range []string{"none", "duplicate_funding", "wrong_credit", "donor_nonce", "recipient_nonce", "storage", "code", "empty_lock_insert", "other_asset", "deleted_account", "existing_recipient", "extra_account", "duplicate_difference", "same_owner", "wrong_ledger"} {
		t.Run(damage, func(t *testing.T) {
			donor, successor := common.Address{1}, common.Address{2}
			before := state.Account{Nonce: 9, BalancesHash: []common.Hash{common.SystemAssetID, common.Hash{3}}, BalancesVal: []*big.Int{big.NewInt(7), big.NewInt(11)}, Root: common.Hash{4}, CodeHash: []byte{5}}
			after := before
			after.BalancesVal = []*big.Int{new(big.Int), big.NewInt(11)}
			credit := state.Account{Nonce: 9, BalancesHash: []common.Hash{common.SystemAssetID}, BalancesVal: []*big.Int{big.NewInt(7)}, Root: types.EmptyRootHash, CodeHash: crypto.Keccak256(nil)}
			switch damage {
			case "duplicate_funding":
				after.BalancesVal[0] = big.NewInt(7)
			case "wrong_credit":
				credit.BalancesVal[0] = big.NewInt(8)
			case "donor_nonce":
				after.Nonce++
			case "recipient_nonce":
				credit.Nonce++
			case "storage":
				after.Root = common.Hash{6}
			case "code":
				after.CodeHash = []byte{6}
			case "empty_lock_insert":
				after.TimeLockBalancesHash = []common.Hash{common.SystemAssetID}
				after.TimeLockBalancesVal = []*common.TimeLock{new(common.TimeLock)}
			case "other_asset":
				after.BalancesVal[1] = big.NewInt(12)
			}
			oldRLP, err := rlp.EncodeToBytes(before)
			requireNoError(t, err)
			newRLP, err := rlp.EncodeToBytes(after)
			requireNoError(t, err)
			creditRLP, err := rlp.EncodeToBytes(credit)
			requireNoError(t, err)
			ledger := fullStateHandoverFunding{Donation: donor, Successor: successor, Liquid: "7", Nonce: 9, Differences: []fullStateDifference{{AccountKey: crypto.Keccak256Hash(donor.Bytes()), Before: oldRLP, After: newRLP}, {AccountKey: crypto.Keccak256Hash(successor.Bytes()), After: creditRLP}}}
			switch damage {
			case "deleted_account":
				ledger.Differences[0].After = nil
			case "existing_recipient":
				ledger.Differences[1].Before = creditRLP
			case "extra_account":
				ledger.Differences = append(ledger.Differences, fullStateDifference{AccountKey: common.Hash{9}})
			case "duplicate_difference":
				ledger.Differences[1] = ledger.Differences[0]
			case "same_owner":
				ledger.Successor = donor
			case "wrong_ledger":
				ledger.Liquid = "8"
			}

			err = validateHandoverFunding(ledger)

			if damage == "none" {
				requireNoError(t, err)
			} else if err == nil {
				t.Fatal("accepted unauthorized funding change")
			}
		})
	}
}

func TestHandoverTemporalAccounting(t *testing.T) {
	owner := common.Address{1}
	account := state.Account{BalancesHash: []common.Hash{common.SystemAssetID}, BalancesVal: []*big.Int{big.NewInt(7)}, TimeLockBalancesHash: []common.Hash{common.SystemAssetID}, TimeLockBalancesVal: []*common.TimeLock{common.NewTimeLock(&common.TimeLockItem{StartTime: 10, EndTime: 20, Value: big.NewInt(3)})}}
	tickets := map[common.Hash]common.TicketDisplay{common.Hash{1}: {Owner: owner, StartTime: 15, ExpireTime: 25, Value: big.NewInt(5)}, common.Hash{2}: {Owner: common.Address{2}, StartTime: 1, ExpireTime: 100, Value: big.NewInt(99)}}
	for _, sample := range []struct{ point, value int64 }{{9, 7}, {10, 10}, {15, 15}, {20, 15}, {21, 12}, {25, 12}, {26, 7}} {
		actual := handoverValueAt(account, tickets, owner, uint64(sample.point))
		if actual.Int64() != sample.value {
			t.Fatalf("time=%d expected=%d got=%s", sample.point, sample.value, actual)
		}
	}
	points := handoverTimeBoundaries(9, map[common.Address]state.Account{owner: account}, nil, tickets, nil)
	for _, point := range []uint64{9, 10, 15, 20, 21, 25, 26, 100, 101, common.TimeLockForever} {
		if !points[point] {
			t.Fatalf("missing temporal boundary %d", point)
		}
	}
	if points[1] {
		t.Fatal("included a boundary before accounting window")
	}
}
