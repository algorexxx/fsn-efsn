package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateDifferenceAccounting(t *testing.T) {
	for _, damage := range []string{"none", "duplicate_funding", "other_asset", "storage", "code", "nonce", "wrong_ledger_credit", "wrong_ledger_locks", "deleted_account", "extra_account"} {
		t.Run(damage, func(t *testing.T) {
			db := rawdb.NewMemoryDatabase()
			defer db.Close()
			cache := state.NewDatabase(db)
			s, err := state.New(common.Hash{}, common.Hash{}, cache)
			requireNoError(t, err)
			original, owner := common.HexToAddress("0x1234"), common.HexToAddress("0x5678")
			other := common.HexToHash("0xabc")
			locks := common.NewTimeLock(&common.TimeLockItem{StartTime: 1, EndTime: 100, Value: big.NewInt(3)})
			s.SetBalance(original, common.SystemAssetID, big.NewInt(7))
			s.SetBalance(original, other, big.NewInt(11))
			s.SetTimeLockBalance(original, common.SystemAssetID, new(common.TimeLock).Set(locks))
			s.SetNonce(original, 9)
			s.SetCode(original, []byte{0x60, 0})
			s.SetState(original, common.Hash{1}, common.Hash{2})
			beforeMix := s.SetData(common.TicketKeyAddress, []byte{1})
			before, err := s.Commit(false)
			requireNoError(t, err)
			requireNoError(t, cache.TrieDB().Commit(before, false, nil))
			s, err = state.New(before, beforeMix, cache)
			requireNoError(t, err)
			s.SetBalance(original, common.SystemAssetID, new(big.Int))
			s.SetTimeLockBalance(original, common.SystemAssetID, new(common.TimeLock))
			s.SetBalance(owner, common.SystemAssetID, big.NewInt(7))
			s.SetTimeLockBalance(owner, common.SystemAssetID, new(common.TimeLock).Set(locks))
			s.SetNonce(owner, 9)
			afterMix := s.SetData(common.TicketKeyAddress, []byte{2})
			switch damage {
			case "duplicate_funding":
				s.SetBalance(original, common.SystemAssetID, big.NewInt(7))
			case "other_asset":
				s.SetBalance(original, other, big.NewInt(12))
			case "storage":
				s.SetState(original, common.Hash{1}, common.Hash{3})
			case "code":
				s.SetCode(original, []byte{0x60, 1})
			case "nonce":
				s.SetNonce(original, 10)
			case "deleted_account":
				s.Suicide(original)
			case "extra_account":
				s.SetBalance(common.Address{8}, common.SystemAssetID, big.NewInt(1))
			}
			after, err := s.Commit(false)
			requireNoError(t, err)
			requireNoError(t, cache.TrieDB().Commit(after, false, nil))
			differences, err := fullStateDifferences(cache, before, after)
			requireNoError(t, err)
			ledger := fullStateFixtureLedger{Source: &types.Header{MixDigest: beforeMix}, Parent: &types.Header{MixDigest: afterMix}, OriginalOwner: original, SyntheticOwner: owner, Liquid: "7", Locks: locks, Nonce: 9, Differences: differences}
			if damage == "wrong_ledger_credit" {
				ledger.Liquid = "8"
			}
			if damage == "wrong_ledger_locks" {
				ledger.Locks = common.NewTimeLock(&common.TimeLockItem{StartTime: 1, EndTime: 99, Value: big.NewInt(3)})
			}
			err = validateFullStateSubstitution(ledger)
			if damage == "none" {
				requireNoError(t, err)
			} else if err == nil {
				t.Fatal("accepted unauthorized full-state difference")
			}
			unchanged, err := fullStateDifferences(cache, before, before)
			requireNoError(t, err)
			if len(unchanged) != 0 {
				t.Fatal("identical roots yielded differences")
			}
			foundOwner := false
			for _, change := range differences {
				if change.AccountKey == crypto.Keccak256Hash(owner.Bytes()) {
					foundOwner = true
					if len(change.Before) != 0 {
						t.Fatal("new account unexpectedly existed")
					}
				}
			}
			if !foundOwner {
				t.Fatal("difference iterator omitted inserted account")
			}
		})
	}
}

func TestFullStateContextIntegrity(t *testing.T) {
	encoded, err := os.ReadFile("../../docs/evidence/restart-full-state-2026-09-24/context.rlp")
	requireNoError(t, err)
	var expected types.Header
	requireNoError(t, json.Unmarshal(readRPCObservations(t)[3], &expected))
	for _, damage := range []string{"none", "short", "missing", "parent_link", "height", "end_hash", "body", "uncles", "receipts", "difficulty"} {
		t.Run(damage, func(t *testing.T) {
			var context fullStateContext
			requireNoError(t, rlp.DecodeBytes(encoded, &context))
			switch damage {
			case "short":
				context.Headers = context.Headers[1:]
			case "missing":
				context.Headers[10] = nil
			case "parent_link":
				context.Headers[10].ParentHash = common.Hash{}
			case "height":
				context.Headers[10].Number = big.NewInt(1)
			case "end_hash":
				context.Headers[255].Root = common.Hash{}
			case "body":
				context.Parent = context.Parent.WithBody(nil, nil)
			case "uncles":
				context.Parent = context.Parent.WithBody(context.Parent.Transactions(), []*types.Header{context.Headers[0]})
			case "receipts":
				context.Receipts = nil
			case "difficulty":
				context.TotalDifficulty = new(big.Int)
			}
			err := validateFullStateContext(&context, expected.Hash())
			if damage == "none" {
				requireNoError(t, err)
			} else if err == nil {
				t.Fatal("accepted damaged historical context")
			}
		})
	}
}
