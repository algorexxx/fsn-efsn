package restart

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type coldHeaderHistory struct {
	Anchor *types.Block
	Blocks types.Blocks
}

func TestColdHeaderValidationBoundaries(t *testing.T) {
	if mode := os.Getenv("FUSION_COLD_HEADERS_MODE"); mode != "" {
		checkColdHeaders(t, os.Getenv("FUSION_COLD_HEADERS_PATH"), mode)
		return
	}
	for _, mode := range []string{"headers_only", "headers_receipts", "headers_bodies", "headers_complete", "headers_missing_receipt", "headers_incremental", "invalid_header", "full_import"} {
		t.Run(mode, func(t *testing.T) {
			directory := t.TempDir()
			prepareColdHeaders(t, directory, mode)
			runColdHeaderChild(t, directory, mode)
			if mode == "full_import" {
				runColdHeaderChild(t, directory, "reopen")
			}
		})
	}
}

func prepareColdHeaders(t *testing.T, directory, mode string) {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 16, 16, "cold-headers", false)
	requireNoError(t, err)
	receiver := newFixtureInDatabase(t, common.TimeLockForever, db)
	producer := newFixtureWithExpiry(t, common.TimeLockForever)
	advancePurchaseFixture(t, producer, receiver)
	history := coldHeaderHistory{Anchor: receiver.chain.CurrentBlock(), Blocks: roundTripBlocks(t, buildAnchorBranch(t, producer, 3, 120))}
	config := *receiver.chain.Config()
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: receiver.chain.Genesis().Hash(), ChainID: config.ChainID.Uint64(), Number: history.Anchor.NumberU64(), Hash: history.Anchor.Hash()}
	receiver.chain.Stop()
	rawdb.WriteChainConfig(db, receiver.chain.Genesis().Hash(), &config)
	for i, block := range history.Blocks {
		switch mode {
		case "headers_receipts":
			rawdb.WriteHeader(db, block.Header())
			rawdb.WriteReceipts(db, block.Hash(), block.NumberU64(), producer.chain.GetReceiptsByHash(block.Hash()))
		case "headers_bodies", "headers_complete", "headers_missing_receipt":
			rawdb.WriteBlock(db, block)
			if mode == "headers_complete" || mode == "headers_missing_receipt" && i != 0 {
				rawdb.WriteReceipts(db, block.Hash(), block.NumberU64(), producer.chain.GetReceiptsByHash(block.Hash()))
			}
		}
	}
	encoded, err := rlp.EncodeToBytes(history)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(directory, "history.rlp"), encoded, 0600))
	requireNoError(t, db.Close())
}

func runColdHeaderChild(t *testing.T, directory, mode string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestColdHeaderValidationBoundaries$", "-test.v", "-test.timeout=30s")
	command.Env = append(os.Environ(), "FUSION_COLD_HEADERS_PATH="+directory, "FUSION_COLD_HEADERS_MODE="+mode)
	output, err := command.CombinedOutput()
	t.Logf("cold process %s:\n%s", mode, output)
	if err != nil || strings.Contains(string(output), "WARNING: DATA RACE") {
		t.Fatalf("cold %s failed: %v", mode, err)
	}
}

func checkColdHeaders(t *testing.T, directory, mode string) {
	encoded, err := os.ReadFile(filepath.Join(directory, "history.rlp"))
	requireNoError(t, err)
	var history coldHeaderHistory
	requireNoError(t, rlp.DecodeBytes(encoded, &history))
	for _, block := range history.Blocks {
		if state.GetCachedTickets(block.MixDigest()) != nil {
			t.Fatal("child inherited a future ticket cache")
		}
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 16, 16, "cold-headers", false)
	requireNoError(t, err)
	defer db.Close()
	config := rawdb.ReadChainConfig(db, rawdb.ReadCanonicalHash(db, 0))
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	f := &fixture{db: db, chain: chain, engine: engine}
	if mode == "reopen" {
		requireColdImportedHeaders(t, f, history.Blocks)
		return
	}
	requireCanonicalTip(t, f, history.Anchor)
	for _, block := range history.Blocks {
		if _, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db)); err == nil {
			t.Fatal("receiver already has a successor account state")
		}
		if rawdb.ReadCanonicalHash(db, block.NumberU64()) != (common.Hash{}) {
			t.Fatal("receiver already has a successor canonical index")
		}
	}
	if mode == "full_import" {
		_, err := chain.InsertChain(history.Blocks)
		requireNoError(t, err)
		requireColdImportedHeaders(t, f, history.Blocks)
		return
	}
	headerChain, err := core.NewHeaderChain(db, config, engine, func() bool { return false })
	requireNoError(t, err)
	headers := blockHeaders(history.Blocks)
	wantIndex, wantError := 1, "AddCachedTickets: hash mismatch"
	if mode == "headers_complete" {
		wantIndex, wantError = 0, ""
	}
	if mode == "invalid_header" {
		headers = headers[:2]
		headers[1].GasUsed = headers[1].GasLimit + 1
		wantError = fmt.Sprintf("invalid gasUsed: have %d, gasLimit %d", headers[1].GasUsed, headers[1].GasLimit)
	}
	if mode == "headers_incremental" {
		_, err := chain.InsertHeaderChain(headers[:1], 1)
		requireNoError(t, err)
		headers, wantIndex = headers[1:2], 0
	}
	index, err := headerChain.ValidateHeaderChain(headers, 1)
	message := ""
	if err != nil {
		message = err.Error()
	}
	if index != wantIndex || message != wantError {
		t.Fatalf("cold %s result index=%d err=%q, expected index=%d err=%q", mode, index, message, wantIndex, wantError)
	}
	requireCanonicalTip(t, f, history.Anchor)
	if chain.CurrentFastBlock().Hash() != history.Anchor.Hash() || rawdb.ReadHeadFastBlockHash(db) != history.Anchor.Hash() {
		t.Fatal("header validation changed the fast head")
	}
	wantHeader := history.Anchor.Hash()
	if mode == "headers_incremental" {
		wantHeader = history.Blocks[0].Hash()
	}
	if rawdb.ReadHeadHeaderHash(db) != wantHeader {
		t.Fatal("validation changed the persisted header head")
	}
	t.Logf("cold %s: index=%d err=%q; full/fast heads unchanged, no successor account state supplied", mode, index, message)
}

func requireColdImportedHeaders(t *testing.T, f *fixture, blocks types.Blocks) {
	t.Helper()
	tip := blocks[len(blocks)-1]
	requireCanonicalTip(t, f, tip)
	if f.chain.CurrentHeader().Hash() != tip.Hash() || f.chain.CurrentFastBlock().Hash() != tip.Hash() || rawdb.ReadHeadHeaderHash(f.db) != tip.Hash() || rawdb.ReadHeadFastBlockHash(f.db) != tip.Hash() {
		t.Fatal("full import left inconsistent header/fast heads")
	}
	for _, block := range blocks {
		if rawdb.ReadCanonicalHash(f.db, block.NumberU64()) != block.Hash() {
			t.Fatal("full import lost a canonical block")
		}
		statedb, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(f.db))
		requireNoError(t, err)
		tickets, err := statedb.AllTickets()
		requireNoError(t, err)
		requireNoError(t, state.AddCachedTickets(block.MixDigest(), tickets))
		receipts := f.chain.GetReceiptsByHash(block.Hash())
		if len(receipts) != len(block.Transactions()) || len(receipts) != 1 || receipts[0].Status != types.ReceiptStatusSuccessful {
			t.Fatal("full import lost a successful purchase receipt")
		}
	}
	t.Logf("cold full import/reopen agrees on three canonical blocks, state/ticket commitments, receipts and full/header/fast heads: %s", tip.Hash().Hex())
}
