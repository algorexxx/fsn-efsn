package observe

import (
	"encoding/json"
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func ticketBlockFixture(t *testing.T, height uint64) (*types.Block, types.Receipts) {
	t.Helper()
	_, events := miningTicketFixture(t)
	for _, event := range events {
		if event.Backfill == nil {
			continue
		}
		for _, evidence := range event.Backfill.Blocks {
			block, err := validateBlockEvidence(evidence)
			if err != nil {
				t.Fatal(err)
			}
			if block.NumberU64() == height {
				return block, evidence.Receipts
			}
		}
	}
	t.Fatal("retained block unavailable", height)
	return nil, nil
}

func TestTicketPurchaseNativeOutcomes(t *testing.T) {
	for _, test := range []struct {
		change, kind string
		invalid      bool
	}{{"success", "purchase", false}, {"native_failure", "purchase_failed", false}, {"outer_failure", "purchase_failed", false}, {"missing", "", true}, {"duplicate", "", true}, {"owner", "", true}, {"base", "", true}, {"topic", "", true}, {"failed_with_log", "", true}, {"ambiguous_failure", "", true}} {
		t.Run(test.change, func(t *testing.T) {
			block, receipts := ticketBlockFixture(t, 26)
			tx, receipt := block.Transactions()[0], receipts[0]
			var outcome map[string]interface{}
			if err := json.Unmarshal(receipt.Logs[0].Data, &outcome); err != nil {
				t.Fatal(err)
			}
			switch test.change {
			case "native_failure":
				outcome = map[string]interface{}{"Error": "synthetic native failure"}
			case "outer_failure":
				receipt.Status, receipt.Logs = types.ReceiptStatusFailed, nil
			case "missing":
				receipt.Logs = nil
			case "duplicate":
				receipt.Logs = append(receipt.Logs, receipt.Logs[0])
			case "owner":
				outcome["TicketOwner"] = common.HexToAddress("0x01")
			case "base":
				outcome["Base"] = []byte{1}
			case "topic":
				receipt.Logs[0].Topics = nil
			case "failed_with_log":
				receipt.Status = types.ReceiptStatusFailed
			case "ambiguous_failure":
				outcome["Error"] = "synthetic inconsistent outcome"
			}
			if len(receipt.Logs) > 0 {
				raw, err := json.Marshal(outcome)
				if err != nil {
					t.Fatal(err)
				}
				receipt.Logs[0].Data = raw
			}
			inventory := make(map[common.Hash]common.TicketDisplay)
			expectedInventory := make(map[common.Hash]common.TicketDisplay)
			expected := []TicketEvent(nil)
			if !test.invalid {
				event := TicketEvent{Block: BlockReference{Number: 26, Hash: block.Hash()}, Kind: test.kind, Transaction: tx.Hash()}
				if test.kind == "purchase" {
					event = expectedTicketEvents(t, donation, 26, 26)[0]
					expectedInventory[event.TicketID] = *event.Ticket
				}
				expected = []TicketEvent{event}
			}

			actual, err := deriveTicketTransaction(donation, inventory, block, tx, receipt)

			if (err != nil) != test.invalid || !reflect.DeepEqual(actual, expected) || !reflect.DeepEqual(inventory, expectedInventory) {
				t.Fatalf("native outcome differs: %v %+v", err, actual)
			}
		})
	}
}

func TestTicketReportRemovesOwnedTickets(t *testing.T) {
	key, err := crypto.HexToECDSA("0000000000000000000000000000000000000000000000000000000000000001")
	if err != nil {
		t.Fatal(err)
	}
	payload, err := rlp.EncodeToBytes(common.FSNCallParam{Func: common.ReportIllegalFunc, Data: []byte{1}})
	if err != nil {
		t.Fatal(err)
	}
	tx, err := types.SignTx(types.NewTransaction(0, common.FSNCallAddress, big.NewInt(0), 100000, big.NewInt(1), payload), types.LatestSignerForChainID(big.NewInt(55555)), key)
	if err != nil {
		t.Fatal(err)
	}
	block := types.NewBlockWithHeader(&types.Header{Number: big.NewInt(30), Time: 200})
	owned, foreign := common.HexToHash("0x01"), common.HexToHash("0x02")
	ticket := common.TicketDisplay{Owner: donation, Height: 1, StartTime: 1, ExpireTime: 500, Value: common.TicketPrice(big.NewInt(1))}
	ids, err := rlp.EncodeToBytes([]common.Hash{foreign, owned})
	if err != nil {
		t.Fatal(err)
	}
	data, err := json.Marshal(map[string]interface{}{"DeleteTickets": hexutil.Bytes(ids)})
	if err != nil {
		t.Fatal(err)
	}
	receipt := &types.Receipt{Status: types.ReceiptStatusSuccessful, Logs: []*types.Log{{Address: common.FSNCallAddress, Topics: []common.Hash{common.BytesToHash([]byte{byte(common.ReportIllegalFunc)})}, Data: data}}}
	inventory := map[common.Hash]common.TicketDisplay{owned: ticket}
	expected := []TicketEvent{{Block: BlockReference{Number: 30, Hash: block.Hash()}, Kind: "report_removal", Transaction: tx.Hash(), TicketID: owned, Ticket: &ticket, Return: "none_report_penalty"}}

	actual, err := deriveTicketTransaction(donation, inventory, block, tx, receipt)

	if err != nil || !reflect.DeepEqual(actual, expected) || len(inventory) != 0 {
		t.Fatalf("foreign reporter did not remove owned ticket: %v %+v", err, actual)
	}
}

func TestTicketRemovalReturnRulesAndParentExpiry(t *testing.T) {
	for _, test := range []struct{ change, selectedReturn string }{{"ordinary", "interval_rights"}, {"genesis", "none_genesis_ticket"}, {"expired", "none_expired_at_block"}} {
		t.Run(test.change, func(t *testing.T) {
			block, receipts := ticketBlockFixture(t, 25)
			config, source := miningTicketFixture(t)
			parent := source[0].Report.Nodes[1].Head.Header
			inventory := source[0].Report.Nodes[1].Tickets
			expected := expectedTicketEvents(t, config.Nodes[1].Wallet, 25, 25)
			selectedID := expected[0].TicketID
			selected := inventory[selectedID]
			if test.change == "genesis" {
				selected.Height = 0
			}
			if test.change == "expired" {
				selected.ExpireTime = block.Time()
			}
			inventory[selectedID], expected[0].Ticket, expected[0].Return = selected, &selected, test.selectedReturn
			expiredID, currentID := common.HexToHash("0x01"), common.HexToHash("0x02")
			expired := common.TicketDisplay{Owner: donation, Height: 1, StartTime: 1, ExpireTime: parent.Time, Value: common.TicketPrice(big.NewInt(1))}
			current := expired
			current.ExpireTime = block.Time()
			inventory[expiredID], inventory[currentID] = expired, current
			expected = append(expected, TicketEvent{Block: BlockReference{Number: 25, Hash: block.Hash()}, Kind: "expiry", TicketID: expiredID, Ticket: &expired, Return: "none_expired_at_parent"})
			expectedInventory := expectedTicketInventory(t, 25, donation)
			expectedInventory[currentID] = current
			original, err := json.Marshal(inventory)
			if err != nil {
				t.Fatal(err)
			}

			actualInventory, actual, err := deriveTicketBlock(donation, inventory, parent, block, receipts)
			after, encodeErr := json.Marshal(inventory)

			if err != nil || encodeErr != nil || !reflect.DeepEqual(actual, expected) || !reflect.DeepEqual(actualInventory, expectedInventory) || string(original) != string(after) {
				t.Fatalf("timestamp/return attribution differs: %v %+v", err, actual)
			}
		})
	}
}

func TestTicketBlockUnsupportedEvidenceIsAtomic(t *testing.T) {
	for _, change := range []string{"receipt_gap", "selection_owner", "vote1", "timestamp", "snapshot_unavailable"} {
		t.Run(change, func(t *testing.T) {
			block, receipts := ticketBlockFixture(t, 26)
			parentBlock, _ := ticketBlockFixture(t, 25)
			parent := parentBlock.Header()
			inventory := expectedTicketInventory(t, 25, donation)
			header := block.Header()
			switch change {
			case "receipt_gap":
				receipts = nil
			case "selection_owner":
				header.Coinbase = common.HexToAddress("0x01")
			case "vote1":
				header.Number = big.NewInt(786000)
			case "timestamp":
				parent.Time = block.Time() + 1
			case "snapshot_unavailable":
				header.Extra = nil
			}
			block = types.NewBlockWithHeader(header).WithBody(block.Transactions(), nil)
			original, err := json.Marshal(inventory)
			if err != nil {
				t.Fatal(err)
			}

			actualInventory, actual, err := deriveTicketBlock(donation, inventory, parent, block, receipts)
			after, encodeErr := json.Marshal(inventory)

			if err == nil || encodeErr != nil || actual != nil || actualInventory != nil || string(original) != string(after) {
				t.Fatal("partial block accounting escaped unsupported evidence", err)
			}
		})
	}
}
