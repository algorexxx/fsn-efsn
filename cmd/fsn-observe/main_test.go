package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func TestCommandRequiresExplicitInputs(t *testing.T) {
	for _, args := range [][]string{nil, {"--config", "missing"}, {"--timeout", "1s"}, {"--config", "missing", "--timeout", "-1s"}, {"--config", "missing", "--timeout", "1s", "extra"}} {
		var output bytes.Buffer
		if run(context.Background(), args, &output, &output) == nil {
			t.Fatal("invalid command accepted", args)
		}
	}
	var help bytes.Buffer
	if run(context.Background(), []string{"--help"}, &help, &help) != nil || !strings.Contains(help.String(), "timeout") {
		t.Fatal("help failed")
	}
}

func TestCommandHistoryLifecycle(t *testing.T) {
	var requests atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		var call struct{ ID json.RawMessage }
		if err := json.NewDecoder(r.Body).Decode(&call); err != nil {
			t.Error(err)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{"jsonrpc": "2.0", "id": call.ID, "error": map[string]interface{}{"code": -32000, "message": "synthetic unavailable read"}})
	}))
	defer server.Close()
	config := observe.Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash("0x1"), AnchorNumber: 1, AnchorHash: common.HexToHash("0x2"), Nodes: []observe.NodeConfig{{Name: "producer", Role: "producer", Wallet: common.HexToAddress("0x1"), Endpoint: strings.Replace(server.URL, "http://", "http://user:secret@", 1)}}}
	directory := t.TempDir()
	configPath, historyPath := filepath.Join(directory, "config.json"), filepath.Join(directory, "history")
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
	invoke("--config", configPath, "--history", historyPath, "--init-history", "--history-budget", "1048576")
	if requests.Load() != 0 {
		t.Fatal("initialization contacted node")
	}
	sample := invoke("--config", configPath, "--timeout", "1s", "--history", historyPath)
	var observation struct {
		observe.Report
		History observe.HistoryStatus
	}
	if err := json.Unmarshal(sample, &observation); err != nil {
		t.Fatal(err)
	}
	if observation.History.Sequence != 1 || len(observation.History.Incidents) != 1 || observation.Nodes[0].Head != nil {
		t.Fatal("failed reads were not durably recorded")
	}
	count := requests.Load()
	if count == 0 {
		t.Fatal("sample did not exercise transport")
	}
	id := observation.History.Incidents[0].ID
	invoke("--history", historyPath, "--history-status")
	invoke("--history", historyPath, "--history-action", "acknowledge", "--incident", id, "--at-sequence", "1", "--reason", "Synthetic operator acknowledged loss of coverage.")
	invoke("--history", historyPath, "--history-action", "resolve", "--incident", id, "--at-sequence", "2", "--reason", "Synthetic review only; a further failed read must reopen this.")
	export := invoke("--history", historyPath, "--history-export")
	if requests.Load() != count || bytes.Contains(export, []byte("secret")) || bytes.Contains(export, []byte("Endpoint")) {
		t.Fatal("offline history command contacted node or leaked endpoint credentials")
	}
	sample = invoke("--config", configPath, "--timeout", "1s", "--history", historyPath)
	if err := json.Unmarshal(sample, &observation); err != nil {
		t.Fatal(err)
	}
	incident := observation.History.Incidents[0]
	if observation.History.Sequence != 4 || incident.Status != "open" || incident.Occurrences != 2 || incident.ID != id {
		t.Fatal("persistent observation did not reopen reviewed incident")
	}
	for _, args := range [][]string{
		{"--config", configPath, "--timeout", "1s", "--backfill-node", "producer", "--backfill-blocks", "1"},
		{"--history", historyPath, "--history-status", "--backfill-node", "producer", "--backfill-blocks", "1"},
		{"--config", configPath, "--timeout", "1s", "--history", historyPath, "--backfill-blocks", "1"},
		{"--config", configPath, "--timeout", "1s", "--history", historyPath, "--backfill-node", "producer", "--backfill-blocks", "129"},
		{"--config", configPath, "--timeout", "1s", "--history", historyPath, "--backfill-node", "missing", "--backfill-blocks", "1"},
		{"--history", historyPath, "--history-status", "--history-export"},
		{"--history", historyPath, "--history-status", "--timeout", "1s"},
		{"--history", historyPath, "--history-budget", "1024"},
		{"--history", historyPath, "--history-action", "resolve", "--incident", id, "--reason", "Missing expected sequence"},
		{"--history", historyPath, "--history-action", "resolve", "--incident", id, "--at-sequence", "1", "--reason", "Stale view"},
	} {
		if err := run(context.Background(), args, &bytes.Buffer{}, &bytes.Buffer{}); err == nil {
			t.Fatal("unsafe flag combination accepted", fmt.Sprint(args))
		}
	}
	backfill := invoke("--config", configPath, "--timeout", "1s", "--history", historyPath, "--backfill-node", "producer", "--backfill-blocks", "1")
	var coverage observe.HistoryStatus
	if json.Unmarshal(backfill, &coverage) != nil || coverage.Sequence != 5 || len(coverage.Blocks) != 1 || coverage.Blocks[0].Status != "unavailable" || coverage.Blocks[0].StoredThrough.Number != 1 {
		t.Fatal("failed backfill was not durably reported", string(backfill))
	}
}

func TestCommandEmitsReportWithoutEndpointSecrets(t *testing.T) {
	config := observe.Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash("0x1"), AnchorNumber: 1, AnchorHash: common.HexToHash("0x2"), Nodes: []observe.NodeConfig{{Name: "retired-backup", Role: "retired", Wallet: common.HexToAddress("0x1"), Endpoint: "https://user:secret@example.invalid/?token=hidden"}}}
	data, err := json.Marshal(config)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "config.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	var output, diagnostics bytes.Buffer
	if err := run(context.Background(), []string{"--config", path, "--timeout", "1s"}, &output, &diagnostics); err != nil {
		t.Fatal(err)
	}
	var report observe.Report
	if json.Unmarshal(output.Bytes(), &report) != nil || report.Version != 1 || report.Nodes[0].Consistency != "not_applicable" || report.Nodes[0].SavedIntent != "unknown" {
		t.Fatal(output.String())
	}
	if strings.Contains(output.String(), "secret") || strings.Contains(output.String(), "hidden") || diagnostics.Len() != 0 {
		t.Fatal("unexpected output")
	}
}
