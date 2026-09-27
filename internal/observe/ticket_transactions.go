package observe

import (
	"bytes"
	"encoding/json"
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func deriveTicketTransaction(wallet common.Address, inventory map[common.Hash]common.TicketDisplay, block *types.Block, tx *types.Transaction, receipt *types.Receipt) ([]TicketEvent, error) {
	var nativeLogs []*types.Log
	for _, entry := range receipt.Logs {
		if entry.Address == common.FSNCallAddress {
			nativeLogs = append(nativeLogs, entry)
		}
	}
	if tx.To() == nil || *tx.To() != common.FSNCallAddress {
		if len(nativeLogs) != 0 {
			return nil, fmt.Errorf("native logs outside a direct native call")
		}
		return nil, nil
	}
	var envelope common.FSNCallParam
	if rlp.DecodeBytes(tx.Data(), &envelope) != nil || envelope.Func > common.ReportIllegalFunc || len(receipt.PostState) != 0 {
		return nil, fmt.Errorf("unsupported native payload or receipt outcome")
	}
	for _, entry := range nativeLogs {
		if len(entry.Topics) != 1 || entry.Topics[0] != common.BytesToHash([]byte{byte(envelope.Func)}) {
			return nil, fmt.Errorf("native log function differs from transaction")
		}
	}
	if envelope.Func != common.BuyTicketFunc && envelope.Func != common.ReportIllegalFunc {
		return nil, nil
	}
	owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
	if err != nil {
		return nil, fmt.Errorf("native sender unavailable")
	}
	reference := BlockReference{Number: block.NumberU64(), Hash: block.Hash()}
	kind := "purchase_failed"
	if envelope.Func == common.ReportIllegalFunc {
		kind = "report_failed"
	}
	if receipt.Status == types.ReceiptStatusFailed {
		if len(nativeLogs) != 0 {
			return nil, fmt.Errorf("failed outer receipt contains native logs")
		}
		if owner == wallet {
			return []TicketEvent{{Block: reference, Kind: kind, Transaction: tx.Hash()}}, nil
		}
		return nil, nil
	}
	if len(nativeLogs) != 1 {
		return nil, fmt.Errorf("native ticket outcome is missing or ambiguous")
	}
	var outcome struct {
		Base          []byte
		TicketID      common.Hash
		TicketOwner   common.Address
		DeleteTickets hexutil.Bytes
		Error         json.RawMessage
	}
	if json.Unmarshal(nativeLogs[0].Data, &outcome) != nil {
		return nil, fmt.Errorf("native ticket outcome cannot be decoded")
	}
	if outcome.Error != nil {
		var reason string
		if json.Unmarshal(outcome.Error, &reason) != nil || reason == "" || outcome.TicketID != (common.Hash{}) || outcome.TicketOwner != (common.Address{}) || outcome.DeleteTickets != nil {
			return nil, fmt.Errorf("native failure outcome is inconsistent")
		}
		if owner == wallet {
			return []TicketEvent{{Block: reference, Kind: kind, Transaction: tx.Hash()}}, nil
		}
		return nil, nil
	}
	if envelope.Func == common.BuyTicketFunc {
		parentHash := block.ParentHash()
		id := crypto.Keccak256Hash(owner[:], parentHash[:])
		var interval common.BuyTicketParam
		if outcome.TicketID != id || outcome.TicketOwner != owner || outcome.DeleteTickets != nil || !bytes.Equal(outcome.Base, envelope.Data) || rlp.DecodeBytes(envelope.Data, &interval) != nil || interval.Start >= interval.End || tx.Value().Sign() != 0 {
			return nil, fmt.Errorf("native purchase does not bind to signed bytes")
		}
		if owner != wallet {
			return nil, nil
		}
		if _, exists := inventory[id]; exists {
			return nil, fmt.Errorf("duplicate owned ticket purchase")
		}
		ticket := common.TicketDisplay{Owner: owner, Height: block.NumberU64(), StartTime: interval.Start, ExpireTime: interval.End, Value: common.TicketPrice(block.Number())}
		inventory[id] = ticket
		return []TicketEvent{{Block: reference, Kind: "purchase", Transaction: tx.Hash(), TicketID: id, Ticket: &ticket}}, nil
	}
	var ids []common.Hash
	if outcome.TicketID != (common.Hash{}) || outcome.TicketOwner != (common.Address{}) || rlp.DecodeBytes(outcome.DeleteTickets, &ids) != nil {
		return nil, fmt.Errorf("report ticket deletions cannot be decoded")
	}
	seen := make(map[common.Hash]bool)
	var events []TicketEvent
	for _, id := range ids {
		if id == (common.Hash{}) || seen[id] {
			return nil, fmt.Errorf("report ticket deletions contain duplicate or empty IDs")
		}
		seen[id] = true
		if ticket, owned := inventory[id]; owned {
			events = append(events, TicketEvent{Block: reference, Kind: "report_removal", Transaction: tx.Hash(), TicketID: id, Ticket: &ticket, Return: "none_report_penalty"})
			delete(inventory, id)
		}
	}
	return events, nil
}
