package core

import (
	"bytes"
	"encoding/json"
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

func CheckRestoredState(db ethdb.Database, expected *params.ChainConfig, genesis common.Hash) error {
	if rawdb.ReadCanonicalHash(db, 0) != genesis {
		return fmt.Errorf("restored startup: genesis mismatch")
	}
	stored := rawdb.ReadChainConfig(db, genesis)
	if stored == nil || stored.DaTong == nil || expected == nil || expected.DaTong == nil {
		return fmt.Errorf("restored startup: missing DaTong configuration")
	}
	want, err := json.Marshal(expected)
	if err != nil {
		return err
	}
	have, err := json.Marshal(stored)
	if err != nil {
		return err
	}
	if !bytes.Equal(have, want) {
		return fmt.Errorf("restored startup: stored configuration mismatch")
	}
	anchor, err := newRestartAnchor(db, expected)
	if err != nil {
		return err
	}
	if anchor == nil {
		return fmt.Errorf("restored startup: missing restart anchor")
	}
	if err := anchor.preflight(); err != nil {
		return err
	}
	hash := rawdb.ReadHeadBlockHash(db)
	number := rawdb.ReadHeaderNumber(db, hash)
	if number == nil || *number == 0 || rawdb.ReadCanonicalHash(db, *number) != hash {
		return fmt.Errorf("restored startup: full head is not a restored canonical block")
	}
	head := rawdb.ReadHeader(db, hash, *number)
	statedb, err := state.New(head.Root, head.MixDigest, state.NewDatabase(db))
	if err != nil {
		return fmt.Errorf("restored startup: head state unavailable: %w", err)
	}
	blob := statedb.GetData(common.TicketKeyAddress)
	if err := statedb.Error(); err != nil {
		return fmt.Errorf("restored startup: ticket data unavailable: %w", err)
	}
	if crypto.Keccak256Hash(blob) != head.MixDigest {
		return fmt.Errorf("restored startup: ticket storage commitment mismatch")
	}
	tickets, err := statedb.AllTickets()
	if err != nil {
		return fmt.Errorf("restored startup: tickets unavailable: %w", err)
	}
	if err := state.AddCachedTickets(head.MixDigest, tickets); err != nil {
		return fmt.Errorf("restored startup: ticket encoding mismatch: %w", err)
	}
	return statedb.Error()
}
