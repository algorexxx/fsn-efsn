package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type fullStateBlockLedger struct {
	Header      *types.Header
	Receipts    types.Receipts
	Tickets     map[common.Hash]common.TicketDisplay
	Differences []fullStateDifference
}

func requireFullStateCopy(t *testing.T, directory string) {
	t.Helper()
	proof, err := os.ReadFile(filepath.Join(directory, "copy-verified.json"))
	requireNoError(t, err)
	var copyProof struct {
		Source         string
		ManifestSHA256 string
		Files          int
	}
	requireNoError(t, json.Unmarshal(proof, &copyProof))
	if filepath.Clean(copyProof.Source) == filepath.Clean(directory) || copyProof.ManifestSHA256 != "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf" || copyProof.Files != 230 {
		t.Fatal("disposable copy proof missing or unexpected")
	}
}

func prepareFullStateCopy(t *testing.T, directory string) {
	t.Helper()
	if _, err := os.Stat(filepath.Join(directory, "fixture.json")); !os.IsNotExist(err) {
		t.Fatal("fixture already initialized or cannot be inspected")
	}
	var identity stateExportIdentity
	encoded, err := os.ReadFile(filepath.Join(directory, "identity.json"))
	requireNoError(t, err)
	requireNoError(t, json.Unmarshal(encoded, &identity))
	var expected types.Header
	requireNoError(t, json.Unmarshal(readRPCObservations(t)[3], &expected))
	if identity.Format != 1 || identity.Head == nil || identity.Head.Hash() != expected.Hash() || identity.Config == nil || identity.Config.RestartAnchor != nil {
		t.Fatal("unexpected state identity or active anchor")
	}
	var context fullStateContext
	encoded, err = os.ReadFile("../../docs/evidence/restart-full-state-2026-09-24/context.rlp")
	requireNoError(t, err)
	requireNoError(t, rlp.DecodeBytes(encoded, &context))
	requireNoError(t, validateFullStateContext(&context, expected.Hash()))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 256, 128, "full-state-prepare", false)
	requireNoError(t, err)
	defer db.Close()
	if rawdb.ReadCanonicalHash(db, 0) != (common.Hash{}) || rawdb.ReadHeadBlockHash(db) != (common.Hash{}) || rawdb.ReadHeadHeaderHash(db) != (common.Hash{}) || rawdb.ReadHeadFastBlockHash(db) != (common.Hash{}) {
		t.Fatal("copy already contains chain metadata")
	}
	ledger := initializeFullStateFixture(t, db, identity, &context)
	requireNoError(t, writeStateExportJSON(filepath.Join(directory, "fixture.json"), ledger))
	t.Logf("synthetic parent=%s root=%s tickets=%s transferredLiquid=%s nonce=%d reassignedTickets=%d changedAccounts=%d", ledger.Parent.Hash().Hex(), ledger.Parent.Root.Hex(), ledger.Parent.MixDigest.Hex(), ledger.Liquid, ledger.Nonce, len(ledger.ReassignedTickets), len(ledger.Differences))
}

func captureFullStateBlock(t *testing.T, f *fixture, parentRoot common.Hash, block *types.Block) fullStateBlockLedger {
	t.Helper()
	s, err := f.chain.StateAt(block.Root(), block.MixDigest())
	requireNoError(t, err)
	tickets, err := s.AllTickets()
	requireNoError(t, err)
	requireNoError(t, state.AddCachedTickets(block.MixDigest(), tickets))
	differences, err := fullStateDifferences(state.NewDatabase(f.db), parentRoot, block.Root())
	requireNoError(t, err)
	receipts := rawdb.ReadReceipts(f.db, block.Hash(), block.NumberU64(), f.chain.Config())
	if len(receipts) != len(block.Transactions()) {
		t.Fatal("receipt count differs from transactions")
	}
	for _, receipt := range receipts {
		if receipt.Status != types.ReceiptStatusSuccessful {
			t.Fatal("recovery purchase failed")
		}
	}
	return fullStateBlockLedger{Header: block.Header(), Receipts: receipts, Tickets: tickets.ToMap(), Differences: differences}
}

func verifyFullStateContextReads(t *testing.T, f *fixture, parent *types.Header) {
	t.Helper()
	next := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number, big.NewInt(1)), Time: parent.Time + 120, Difficulty: big.NewInt(1)}
	context := core.NewEVMBlockContext(next, f.chain, &f.owner)
	if context.ParentTime.Uint64() != parent.Time {
		t.Fatal("missing EVM parent time")
	}
	for depth := uint64(0); depth < 256; depth++ {
		height := parent.Number.Uint64() - depth
		header := f.chain.GetHeaderByNumber(height)
		if header == nil || context.GetHash(height) != header.Hash() {
			t.Fatalf("missing or inconsistent historical context at %d", height)
		}
	}
	if f.chain.GetHeaderByNumber(parent.Number.Uint64()-10) == nil {
		t.Fatal("missing sealing-delay context")
	}
}
