package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type fullStateAccountLedger struct {
	AccountKey common.Hash
	Address    *common.Address `json:",omitempty"`
	Before     state.Account
	After      state.Account
}

type fullStateAccounting struct {
	Number         uint64
	Hash           common.Hash
	Time           uint64
	Tickets        int
	LiquidIncrease string
	Accounts       []fullStateAccountLedger
}

func TestFullStateLedgerAudit(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_FULL_STATE_LEDGER")
	if directory == "" {
		t.Skip("set FUSION_RESTART_FULL_STATE_LEDGER to the prepared copy for independent ledger accounting")
	}
	artifacts := os.Getenv("FUSION_RESTART_FULL_STATE_BLOCKS")
	output := os.Getenv("FUSION_RESTART_FULL_STATE_ACCOUNTING")
	if !filepath.IsAbs(directory) || !filepath.IsAbs(artifacts) || !filepath.IsAbs(output) {
		t.Fatal("absolute ledger, block and new output paths required")
	}
	var fixture fullStateFixtureLedger
	encoded, err := os.ReadFile(filepath.Join(directory, "fixture.json"))
	requireNoError(t, err)
	requireNoError(t, json.Unmarshal(encoded, &fixture))
	requireNoError(t, validateFullStateSubstitution(fixture))
	addresses := make(map[common.Hash]common.Address)
	var historicalTickets map[common.Hash]common.TicketDisplay
	requireNoError(t, json.Unmarshal(readRPCObservations(t)[7], &historicalTickets))
	for _, ticket := range historicalTickets {
		addresses[crypto.Keccak256Hash(ticket.Owner.Bytes())] = ticket.Owner
	}
	for _, address := range []common.Address{fixture.OriginalOwner, fixture.SyntheticOwner, common.TicketKeyAddress} {
		addresses[crypto.Keccak256Hash(address.Bytes())] = address
	}
	var accounting []fullStateAccounting
	previous := fixture.Parent.Hash()
	for i := 1; i <= 8; i++ {
		var entry fullStateBlockLedger
		encoded, err := os.ReadFile(filepath.Join(artifacts, fmt.Sprintf("block-%02d.json", i)))
		requireNoError(t, err)
		requireNoError(t, json.Unmarshal(encoded, &entry))
		if entry.Header.ParentHash != previous {
			t.Fatal("ledger parent link differs")
		}
		previous = entry.Header.Hash()
		result := fullStateAccounting{Number: entry.Header.Number.Uint64(), Hash: previous, Time: entry.Header.Time, Tickets: len(entry.Tickets)}
		increase := new(big.Int)
		for _, change := range entry.Differences {
			account := fullStateAccountLedger{AccountKey: change.AccountKey}
			requireNoError(t, rlp.DecodeBytes(change.Before, &account.Before))
			requireNoError(t, rlp.DecodeBytes(change.After, &account.After))
			if address, ok := addresses[change.AccountKey]; ok {
				account.Address = &address
			} else {
				t.Fatal("bridge changed an account outside the signer, historical ticket owners and ticket store")
			}
			requireNoError(t, validateFullStateBlockAccount(account, fixture.SyntheticOwner, i > 1))
			for j, asset := range account.Before.BalancesHash {
				if asset == common.SystemAssetID {
					increase.Sub(increase, account.Before.BalancesVal[j])
				}
			}
			for j, asset := range account.After.BalancesHash {
				if asset == common.SystemAssetID {
					increase.Add(increase, account.After.BalancesVal[j])
				}
			}
			result.Accounts = append(result.Accounts, account)
		}
		if increase.String() != "312500000000000000" {
			t.Fatalf("unexpected aggregate liquid change at step %d: %s", i, increase)
		}
		result.LiquidIncrease = increase.String()
		if i == 1 && len(entry.Receipts) != 0 {
			t.Fatal("unexpected first-block transactions")
		}
		if i > 1 {
			if len(entry.Receipts) != 1 {
				t.Fatal("expected one replenishment purchase")
			}
			receipt := entry.Receipts[0]
			if receipt.Status != types.ReceiptStatusSuccessful || len(receipt.Logs) != 1 {
				t.Fatal("purchase receipt failed or ambiguous")
			}
			log := receipt.Logs[0]
			if log.Address != common.FSNCallAddress || len(log.Topics) != 1 || log.Topics[0] != common.BytesToHash([]byte{common.BuyTicketFunc}) {
				t.Fatal("wrong native purchase log")
			}
			var payload map[string]json.RawMessage
			requireNoError(t, json.Unmarshal(log.Data, &payload))
			if _, exists := payload["Error"]; exists {
				t.Fatal("native purchase reports error despite receipt status")
			}
			var id common.Hash
			var owner common.Address
			requireNoError(t, json.Unmarshal(payload["TicketID"], &id))
			requireNoError(t, json.Unmarshal(payload["TicketOwner"], &owner))
			ticket, ok := entry.Tickets[id]
			if !ok || owner != fixture.SyntheticOwner || ticket.Owner != owner || ticket.Height != result.Number || ticket.Value.String() != "5000000000000000000000" {
				t.Fatal("purchase does not match live 5000 FSN ticket")
			}
		}
		accounting = append(accounting, result)
		t.Logf("step=%d height=%d hash=%s accounts=%d tickets=%d aggregateLiquidIncrease=%s", i, result.Number, result.Hash.Hex(), len(result.Accounts), result.Tickets, result.LiquidIncrease)
	}
	requireNoError(t, writeStateExportJSON(output, accounting))
	t.Log("all eight self-produced blocks add exactly 0.3125 FSN each; seven purchases and unrelated account fields verified")
}

func validateFullStateBlockAccount(account fullStateAccountLedger, signer common.Address, purchase bool) error {
	before, after := account.Before, account.After
	before.BalancesVal = append([]*big.Int(nil), before.BalancesVal...)
	after.BalancesVal = append([]*big.Int(nil), after.BalancesVal...)
	before.TimeLockBalancesVal = append([]*common.TimeLock(nil), before.TimeLockBalancesVal...)
	after.TimeLockBalancesVal = append([]*common.TimeLock(nil), after.TimeLockBalancesVal...)
	if account.AccountKey == crypto.Keccak256Hash(common.TicketKeyAddress.Bytes()) {
		before.CodeHash = after.CodeHash
	} else {
		for i, asset := range before.TimeLockBalancesHash {
			if asset == common.SystemAssetID {
				before.TimeLockBalancesVal[i] = nil
			}
		}
		for i, asset := range after.TimeLockBalancesHash {
			if asset == common.SystemAssetID {
				after.TimeLockBalancesVal[i] = nil
			}
		}
		if account.AccountKey == crypto.Keccak256Hash(signer.Bytes()) {
			for i, asset := range before.BalancesHash {
				if asset == common.SystemAssetID {
					before.BalancesVal[i] = nil
				}
			}
			for i, asset := range after.BalancesHash {
				if asset == common.SystemAssetID {
					after.BalancesVal[i] = nil
				}
			}
			if purchase {
				before.Nonce++
			}
		}
	}
	a, err := rlp.EncodeToBytes(&before)
	if err != nil {
		return err
	}
	b, err := rlp.EncodeToBytes(&after)
	if err != nil {
		return err
	}
	if !bytes.Equal(a, b) {
		return fmt.Errorf("unexpected field change at %s", account.AccountKey.Hex())
	}
	return nil
}
