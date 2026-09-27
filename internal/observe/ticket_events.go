package observe

import (
	"encoding/binary"
	"fmt"
	"sort"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func deriveTicketBlock(wallet common.Address, previous map[common.Hash]common.TicketDisplay, parent *types.Header, block *types.Block, receipts types.Receipts) (map[common.Hash]common.TicketDisplay, []TicketEvent, error) {
	if len(receipts) != len(block.Transactions()) {
		return nil, nil, fmt.Errorf("ticket evidence lacks transaction receipts")
	}
	if block.Time() < parent.Time || common.IsVote1ForkBlock(block.Number()) {
		return nil, nil, fmt.Errorf("unsupported timestamp or historical Vote1 transition")
	}
	snapshot, err := ticketSnapshot(block.Header())
	if err != nil {
		return nil, nil, err
	}
	inventory := make(map[common.Hash]common.TicketDisplay, len(previous))
	for id, ticket := range previous {
		inventory[id] = ticket
	}
	var events []TicketEvent
	for i, tx := range block.Transactions() {
		native, err := deriveTicketTransaction(wallet, inventory, block, tx, receipts[i])
		if err != nil {
			return nil, nil, err
		}
		events = append(events, native...)
	}
	reference := BlockReference{Number: block.NumberU64(), Hash: block.Hash()}
	for i, id := range append([]common.Hash{snapshot.Selected}, snapshot.Retreat...) {
		ticket, owned := inventory[id]
		if i == 0 && (owned != (block.Coinbase() == wallet)) {
			return nil, nil, fmt.Errorf("selection conflicts with scoped ownership")
		}
		if !owned {
			continue
		}
		if ticket.Height >= block.NumberU64() {
			return nil, nil, fmt.Errorf("removed ticket is not from the parent inventory")
		}
		event := TicketEvent{Block: reference, Kind: "selection", TicketID: id, Ticket: &ticket, Return: "interval_rights"}
		if i > 0 {
			index := i - 1
			event.Kind, event.RetreatIndex = "retreat", &index
		}
		if ticket.Height == 0 {
			event.Return = "none_genesis_ticket"
		} else if i == 1 {
			event.Return = "none_first_retreat"
		} else if ticket.ExpireTime <= block.Time() {
			event.Return = "none_expired_at_block"
		}
		events = append(events, event)
		delete(inventory, id)
	}
	var expired []common.Hash
	for id, ticket := range inventory {
		if ticket.ExpireTime <= parent.Time {
			expired = append(expired, id)
		}
	}
	sort.Slice(expired, func(i, j int) bool { return expired[i].Hex() < expired[j].Hex() })
	for _, id := range expired {
		ticket := inventory[id]
		events = append(events, TicketEvent{Block: reference, Kind: "expiry", TicketID: id, Ticket: &ticket, Return: "none_expired_at_parent"})
		delete(inventory, id)
	}
	if len(inventory) > snapshot.TicketNumber {
		return nil, nil, fmt.Errorf("scoped inventory exceeds header ticket count")
	}
	return inventory, events, nil
}

func ticketSnapshot(header *types.Header) (*datong.Snapshot, error) {
	if len(header.Extra) < 32+5+33+65 {
		return nil, fmt.Errorf("unsupported ticket snapshot framing")
	}
	data := header.Extra[32 : len(header.Extra)-65]
	if (len(data)-5)%33 != 0 || binary.BigEndian.Uint32(data[:4]) > 0x7fffffff {
		return nil, fmt.Errorf("unsupported ticket snapshot count or record framing")
	}
	seen := make(map[common.Hash]bool)
	for offset := 4; offset < len(data)-1; offset += 33 {
		id := common.BytesToHash(data[offset : offset+32])
		kind := byte(2)
		if offset == 4 {
			kind = 1
		}
		if id == (common.Hash{}) || seen[id] || data[offset+32] != kind {
			return nil, fmt.Errorf("unsupported ticket snapshot record type, order or identity")
		}
		seen[id] = true
	}
	return datong.NewSnapshotFromHeader(header)
}
