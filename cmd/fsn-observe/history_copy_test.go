package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"sync/atomic"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func TestCommandHistoryCopyIsOfflineAndExplicit(t *testing.T) {
	var requests atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		http.Error(w, "unexpected request", http.StatusServiceUnavailable)
	}))
	defer server.Close()
	config := observe.Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash("0x1"), AnchorNumber: 1, AnchorHash: common.HexToHash("0x2"), Nodes: []observe.NodeConfig{{Name: "retired-backup", Role: "retired", Wallet: common.HexToAddress("0x1"), Endpoint: server.URL}}}
	directory := t.TempDir()
	configPath, source := filepath.Join(directory, "config.json"), filepath.Join(directory, "history")
	raw, err := json.Marshal(config)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(configPath, raw, 0600); err != nil {
		t.Fatal(err)
	}
	invoke := func(args ...string) []byte {
		t.Helper()
		var output, diagnostics bytes.Buffer
		if err := run(context.Background(), args, &output, &diagnostics); err != nil {
			t.Fatal(err, diagnostics.String())
		}
		return output.Bytes()
	}
	invoke("--config", configPath, "--history", source, "--init-history", "--history-budget", "65536")
	invoke("--config", configPath, "--timeout", "1s", "--history", source)
	before := invoke("--history", source, "--history-export")
	var expected observe.HistoryStatus
	if err := json.Unmarshal(invoke("--history", source, "--history-status"), &expected); err != nil {
		t.Fatal(err)
	}
	expected.MaxBytes, expected.LogicalBytes = 131072, expected.LogicalBytes+1
	destination := filepath.Join(directory, "larger")

	result := invoke("--history", source, "--history-copy", destination, "--history-budget", "131072", "--at-sequence", "1")

	var actual observe.HistoryStatus
	if err := json.Unmarshal(result, &actual); err != nil || !reflect.DeepEqual(actual, expected) {
		t.Fatal("copy status changed evidence", err)
	}
	if !bytes.Equal(result, invoke("--history", destination, "--history-status")) {
		t.Fatal("copy cannot be reopened at returned status")
	}
	after := invoke("--history", destination, "--history-export")
	if !bytes.Equal(bytes.SplitN(before, []byte{'\n'}, 2)[1], bytes.SplitN(after, []byte{'\n'}, 2)[1]) {
		t.Fatal("command copy changed event bytes")
	}
	invoke("--config", configPath, "--timeout", "1s", "--history", destination)
	if err := json.Unmarshal(invoke("--history", destination, "--history-status"), &actual); err != nil || actual.Sequence != 2 {
		t.Fatal("command did not continue copied history", err)
	}
	for _, extra := range [][]string{
		{"--history-status"}, {"--history-export"}, {"--init-history"},
		{"--history-action", "acknowledge"}, {"--incident", "unexpected"}, {"--reason", "unexpected"},
		{"--config", configPath}, {"--timeout", "1s"},
		{"--backfill-node", "retired-backup", "--backfill-blocks", "1"},
		{"--anchor-inventory", "retired-backup"},
		{"--ticket-timeline", "retired-backup", "--ticket-blocks", "1"},
		{"--history-budget", "0"}, {"--at-sequence", "0"}, {"--at-sequence", "2"},
	} {
		args := []string{"--history", source, "--history-copy", filepath.Join(directory, "rejected"), "--history-budget", "131072", "--at-sequence", "1"}
		var output, diagnostics bytes.Buffer
		if err := run(context.Background(), append(args, extra...), &output, &diagnostics); err == nil || output.Len() != 0 {
			t.Fatal("invalid copy flags succeeded or emitted success", extra, err)
		}
	}
	if _, err := os.Stat(filepath.Join(directory, "rejected")); !os.IsNotExist(err) {
		t.Fatal("invalid flags created a destination", err)
	}
	if requests.Load() != 0 || !bytes.Equal(before, invoke("--history", source, "--history-export")) {
		t.Fatal("copy or rejected input contacted endpoint or changed source")
	}
}
