package restart

import (
	"encoding/json"
	"os"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

type inspectionBackup struct {
	db     ethdb.Database
	head   types.Header
	config *params.ChainConfig
}

func openInspectionBackup(t *testing.T) inspectionBackup {
	t.Helper()
	if os.Getenv("FUSION_RESTART_FULL_AUDIT") != "1" {
		t.Skip("set FUSION_RESTART_FULL_AUDIT=1 for the complete read-only integrity scan")
	}
	directory := os.Getenv("FUSION_RESTART_CHAINDATA")
	if directory == "" {
		t.Fatal("FUSION_RESTART_CHAINDATA must name the verified disposable copy")
	}
	var expected types.Header
	requireNoError(t, json.Unmarshal(readRPCObservations(t)[3], &expected))
	db, err := rawdb.NewLevelDBDatabase(directory, 512, 128, "restart-integrity", true)
	requireNoError(t, err)
	t.Cleanup(func() { requireNoError(t, db.Close()) })
	if rawdb.ReadHeadBlockHash(db) != expected.Hash() {
		t.Fatal("database head differs from the observed recovery parent")
	}
	genesis := rawdb.ReadCanonicalHash(db, 0)
	if genesis != common.HexToHash("0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a") {
		t.Fatal("unexpected genesis")
	}
	config := rawdb.ReadChainConfig(db, genesis)
	if config == nil {
		t.Fatal("missing stored chain configuration")
	}
	return inspectionBackup{db: db, head: expected, config: config}
}

func TestPreservedStateIntegrity(t *testing.T) {
	backup := openInspectionBackup(t)
	lastProgress := time.Now()
	result, err := inspectState(backup.db, backup.head.Root, func(current stateInspection) {
		if time.Since(lastProgress) >= 20*time.Second {
			t.Logf("state progress: %+v", current)
			lastProgress = time.Now()
		}
	})
	t.Logf("state result: %+v root=%s error=%v", result, backup.head.Root.Hex(), err)
	requireNoError(t, err)
}

func TestPreservedHistoryIntegrity(t *testing.T) {
	backup := openInspectionBackup(t)
	lastProgress := time.Now()
	result, err := inspectHistory(backup.db, backup.config, backup.head.Number.Uint64(), func(current historyInspection) {
		if time.Since(lastProgress) >= 20*time.Second {
			t.Logf("history progress: blocks=%d transactions=%d receipts=%d exportRLPBytes=%d lastHash=%s", current.Blocks, current.Transactions, current.Receipts, current.ExportRLPBytes, current.LastHash.Hex())
			lastProgress = time.Now()
		}
	})
	t.Logf("history result: blocks=%d transactions=%d receipts=%d exportRLPBytes=%d absentEmptyReceiptRecords=%d lastHash=%s totalDifficulty=%s error=%v", result.Blocks, result.Transactions, result.Receipts, result.ExportRLPBytes, result.AbsentEmptyReceiptRecords, result.LastHash.Hex(), result.TotalDifficulty, err)
	requireNoError(t, err)
	if result.LastHash != backup.head.Hash() {
		t.Fatal("complete scan did not reach the observed recovery parent")
	}
}
