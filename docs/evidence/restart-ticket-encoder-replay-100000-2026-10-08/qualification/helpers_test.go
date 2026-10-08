package restart

import (
"encoding/json"
"os"
"testing"
"github.com/FusionFoundation/efsn/v5/common"
"github.com/FusionFoundation/efsn/v5/core/rawdb"
"github.com/FusionFoundation/efsn/v5/core/types"
"github.com/FusionFoundation/efsn/v5/ethdb"
"github.com/FusionFoundation/efsn/v5/params"
)

type rpcObservation struct {
	ID     int
	Result json.RawMessage
}

func readRPCObservations(t *testing.T) map[int]json.RawMessage {
	t.Helper()
	data, err := os.ReadFile("../../docs/evidence/restart-2026-09-23/responses.json")
	requireNoError(t, err)
	var observations []rpcObservation
	requireNoError(t, json.Unmarshal(data, &observations))
	values := make(map[int]json.RawMessage)
	for _, observation := range observations {
		values[observation.ID] = observation.Result
	}
	return values
}

func requireNoError(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

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

