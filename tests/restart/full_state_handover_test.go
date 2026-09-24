package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateHandover(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_HANDOVER_DIR")
	if directory == "" {
		t.Skip("set FUSION_RESTART_HANDOVER_DIR to a freshly verified disposable state copy")
	}
	if !filepath.IsAbs(directory) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable path and no backup source environment required")
	}
	requireFullStateCopy(t, directory)
	mode := os.Getenv("FUSION_RESTART_HANDOVER_MODE")
	artifacts := os.Getenv("FUSION_RESTART_HANDOVER_BLOCKS")
	if !filepath.IsAbs(artifacts) {
		t.Fatal("absolute handover artifact path required")
	}
	t.Logf("full-state handover mode=%s directory=%s executable=%s", mode, directory, stateExportExecutableHash(t))
	switch mode {
	case "prepare":
		prepareFullStateHandover(t, directory)
	case "produce":
		produceFullStateHandover(t, directory, artifacts)
	case "runtime":
		runFullStateHandoverMiner(t, directory, artifacts)
	case "import", "cold":
		verifyFullStateHandover(t, directory, artifacts, mode)
	default:
		t.Fatal("mode must be prepare, produce, runtime, import or cold")
	}
}

func produceFullStateHandover(t *testing.T, directory, artifacts string) {
	t.Helper()
	f, original, funding := openFullStateHandover(t, directory)
	if f.chain.CurrentBlock().Hash() != funding.Parent.Hash() {
		t.Fatal("handover must start from freshly prepared state")
	}
	requireNoError(t, os.Mkdir(artifacts, 0700))
	successor := *f
	selectHandoverSuccessor(t, &successor, funding)
	pool := f.newPool(t)
	for i := 0; i < 6; i++ {
		parent := f.chain.CurrentBlock()
		verifyFullStateContextReads(t, f, parent.Header())
		timestamp := parent.Time() + 120
		if i == 1 {
			timestamp = jumpTime
		}
		end := parent.Time() + 30*24*3600
		if end < ticketEnd {
			end = ticketEnd
		}
		purchase := successor.signPurchase(t, parent.Time(), end)
		if i == 0 {
			requireNoError(t, pool.AddLocal(purchase))
			t.Log("successor first long-lived purchase admitted to the real transaction pool at the historical head")
		}
		signer := &successor
		if i == 0 {
			signer = f
		}
		block := signer.buildBlockWithTransactions(t, timestamp, []*types.Transaction{purchase})
		f.importBlock(t, block)
		recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
	}
	s, err := f.chain.State()
	requireNoError(t, err)
	tickets, err := s.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTickets() != 1 || tickets.NumberOfTicketsByAddress(funding.Successor) != 1 || s.GetNonce(original.SyntheticOwner) != original.Nonce || s.GetNonce(funding.Successor) != 6 {
		t.Fatal("handover did not leave an independently funded sole successor")
	}
}

func recordFullStateHandoverBlock(t *testing.T, f *fixture, artifacts string, base uint64, block *types.Block) {
	t.Helper()
	parent := f.chain.GetBlockByHash(block.ParentHash())
	if parent == nil {
		t.Fatal("missing recorded parent")
	}
	entry := captureFullStateBlock(t, f, parent.Root(), block)
	index := block.NumberU64() - base
	encoded, err := rlp.EncodeToBytes(block)
	requireNoError(t, err)
	file, err := os.OpenFile(filepath.Join(artifacts, fmt.Sprintf("block-%02d.rlp", index)), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	_, err = file.Write(encoded)
	requireNoError(t, err)
	requireNoError(t, file.Close())
	requireNoError(t, writeStateExportJSON(filepath.Join(artifacts, fmt.Sprintf("block-%02d.json", index)), entry))
	t.Logf("block=%d height=%d time=%d signer=%s hash=%s root=%s tickets=%d changedAccounts=%d", index, block.NumberU64(), block.Time(), block.Coinbase().Hex(), block.Hash().Hex(), block.Root().Hex(), len(entry.Tickets), len(entry.Differences))
}

func verifyFullStateHandover(t *testing.T, directory, artifacts, mode string) {
	t.Helper()
	f, _, funding := openFullStateHandover(t, directory)
	selectHandoverSuccessor(t, f, funding)
	files, err := filepath.Glob(filepath.Join(artifacts, "block-*.rlp"))
	requireNoError(t, err)
	if len(files) != 10 {
		t.Fatalf("expected six constructed and four worker blocks, got %d", len(files))
	}
	if mode == "import" && f.chain.CurrentBlock().Hash() != funding.Parent.Hash() {
		t.Fatal("independent verifier must start at synthetic parent")
	}
	for i, path := range files {
		if filepath.Base(path) != fmt.Sprintf("block-%02d.rlp", i+1) {
			t.Fatal("nonconsecutive handover artifacts")
		}
		encoded, err := os.ReadFile(path)
		requireNoError(t, err)
		var block *types.Block
		requireNoError(t, rlp.DecodeBytes(encoded, &block))
		if mode == "import" {
			f.importBlock(t, block)
		}
		canonical := f.chain.GetBlockByNumber(block.NumberU64())
		if canonical == nil || canonical.Hash() != block.Hash() || block.NumberU64() != funding.Parent.Number.Uint64()+uint64(i)+1 {
			t.Fatal("canonical handover identity mismatch")
		}
		parent := f.chain.GetHeader(block.ParentHash(), block.NumberU64()-1)
		actual := captureFullStateBlock(t, f, parent.Root, block)
		actualJSON, err := json.MarshalIndent(actual, "", "  ")
		requireNoError(t, err)
		expectedJSON, err := os.ReadFile(filepath.Join(artifacts, fmt.Sprintf("block-%02d.json", i+1)))
		requireNoError(t, err)
		if !bytes.Equal(bytes.TrimSpace(expectedJSON), actualJSON) {
			t.Fatal("independent/cold header, receipts, tickets or complete account differences mismatch")
		}
		t.Logf("verified block=%d hash=%s root=%s tickets=%d", i+1, block.Hash().Hex(), block.Root().Hex(), len(actual.Tickets))
	}
	head := f.chain.CurrentBlock()
	if head.NumberU64() != funding.Parent.Number.Uint64()+uint64(len(files)) || rawdb.ReadHeadBlockHash(f.db) != head.Hash() || rawdb.ReadHeadHeaderHash(f.db) != head.Hash() || rawdb.ReadHeadFastBlockHash(f.db) != head.Hash() {
		t.Fatal("handover head markers mismatch")
	}
	verifyFullStateContextReads(t, f, head.Header())
	if mode != "cold" {
		return
	}
	verifyFullStateReconstruction(t, f)
	last := time.Now()
	result, err := inspectState(f.db, head.Root(), func(current stateInspection) {
		if time.Since(last) > 20*time.Second {
			t.Logf("cold handover progress: %+v", current)
			last = time.Now()
		}
	})
	requireNoError(t, err)
	requireNoError(t, writeStateExportJSON(filepath.Join(directory, "handover-cold.json"), result))
	t.Logf("cold complete state: %+v head=%s root=%s", result, head.Hash().Hex(), head.Root().Hex())
}
