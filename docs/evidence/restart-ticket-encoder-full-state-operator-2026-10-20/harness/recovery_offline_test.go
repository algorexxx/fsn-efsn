package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type offlineRecoveryStep struct {
	Plan      recovery.Plan
	Purchase  hexutil.Bytes
	Unsigned  hexutil.Bytes
	Expected  hexutil.Bytes
	Ledger    fullStateBlockLedger
	FullState bool `json:",omitempty"`
}

func writeOfflineRecoverySteps(t *testing.T, directory string, original, successor *fixture, fullState bool) {
	t.Helper()
	for stage := 1; stage <= 3; stage++ {
		parent := original.chain.CurrentBlock()
		signer, timestamp, next := original, parent.Time()+120, jumpTime
		if stage > 1 {
			signer, timestamp, next = successor, jumpTime+uint64(stage-2)*120, jumpTime+uint64(stage-1)*120
		}
		tx := successor.signPurchase(t, parent.Time(), ticketEnd)
		plan := recoveryPlan(t, signer, successor, timestamp, next, tx)
		candidate, err := recovery.Build(original.chain, plan, types.Transactions{tx})
		requireNoError(t, err)
		unsigned, err := rlp.EncodeToBytes(candidate.Block)
		requireNoError(t, err)
		purchase, err := rlp.EncodeToBytes(tx)
		requireNoError(t, err)
		independent := signer.buildBlockWithTransactions(t, timestamp, []*types.Transaction{tx})
		expected, err := rlp.EncodeToBytes(independent)
		requireNoError(t, err)
		original.importBlock(t, independent)
		ledger := captureFullStateBlock(t, original, parent.Root(), independent)
		requireNoError(t, writeStateExportJSON(filepath.Join(directory, fmt.Sprintf("step-%d.json", stage)), offlineRecoveryStep{Plan: plan, Purchase: purchase, Unsigned: unsigned, Expected: expected, Ledger: ledger, FullState: fullState}))
	}
}

func offlineChainPath(t *testing.T, directory, role string, fullState bool) string {
	t.Helper()
	path := filepath.Join(directory, role)
	if fullState {
		requireFullStateCopy(t, path)
		path = filepath.Join(path, "chaindata")
	}
	return path
}

func verifyOfflineImport(t *testing.T, path string, step *offlineRecoveryStep, encoded []byte, allowImport bool, afterImport func()) {
	t.Helper()
	var block types.Block
	requireNoError(t, rlp.DecodeBytes(encoded, &block))
	if !bytes.Equal(encoded, step.Expected) {
		t.Fatal("unreviewed import artifact")
	}
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "offline-import", false)
	requireNoError(t, err)
	defer db.Close()
	reader, err := recovery.NewReader(db)
	requireNoError(t, err)
	head := reader.CurrentHeader().Hash()
	if head != step.Plan.ParentHash && head != block.Hash() {
		t.Fatal("unexpected persisted head before import/startup")
	}
	engine := datong.New(reader.Config().DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, reader.Config(), engine, vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	if chain.CurrentBlock().Hash() != head {
		t.Fatal("startup repaired the offline handover head")
	}
	if head == step.Plan.ParentHash {
		if !allowImport {
			t.Fatal("cold verification lost imported block")
		}
		_, err := chain.InsertChain(types.Blocks{&block})
		requireNoError(t, err)
	}
	if chain.CurrentBlock().Hash() != block.Hash() || chain.CurrentHeader().Hash() != block.Hash() || chain.CurrentFastBlock().Hash() != block.Hash() {
		t.Fatal("imported heads differ")
	}
	parent := chain.GetHeader(block.ParentHash(), block.NumberU64()-1)
	if parent == nil {
		t.Fatal("missing imported parent")
	}
	f := &fixture{db: db, chain: chain, engine: engine}
	if step.FullState {
		verifyFullStateContextReads(t, f, block.Header())
	}
	actual, err := json.Marshal(captureFullStateBlock(t, f, parent.Root, &block))
	requireNoError(t, err)
	want, err := json.Marshal(step.Ledger)
	requireNoError(t, err)
	if !bytes.Equal(actual, want) {
		t.Fatal("cold accounts, receipts, tickets or header differ from independent ledger")
	}
	if afterImport != nil {
		afterImport()
	}
}

func offlineDatabaseFiles(t *testing.T, path string) map[string]string {
	t.Helper()
	entries, err := os.ReadDir(path)
	requireNoError(t, err)
	result := make(map[string]string)
	for _, entry := range entries {
		if entry.IsDir() {
			t.Fatal("unexpected directory in small offline fixture")
		}
		result[entry.Name()] = stateExportFileHash(t, filepath.Join(path, entry.Name()))
	}
	return result
}
