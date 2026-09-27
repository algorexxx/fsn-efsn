package observe

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/syndtr/goleveldb/leveldb/opt"
)

func serviceHistoryInput(t *testing.T, name string, tick int) (Config, Report) {
	t.Helper()
	base := filepath.Join("..", "..", "docs", "evidence", "restart-observer-services-2026-09-27", "attempt-4", "services")
	var config Config
	var report Report
	readFixture(t, filepath.Join(base, name+"-config.json"), &config)
	readFixture(t, filepath.Join(base, name+".json"), &report)
	for i := range config.Nodes {
		config.Nodes[i].Endpoint = fmt.Sprintf("http://127.0.0.1:1/%d", i)
	}
	report.StartedUTC = time.Date(2026, 9, 27, 18, 0, tick*10, 0, time.UTC)
	report.FinishedUTC = report.StartedUTC.Add(3 * time.Second)
	for i := range report.Nodes {
		report.Nodes[i].StartedUTC = report.StartedUTC.Add(time.Second)
		report.Nodes[i].FinishedUTC = report.StartedUTC.Add(2 * time.Second)
	}
	return config, report
}

func findIncident(t *testing.T, state HistoryStatus, node, kind string, hash common.Hash) Incident {
	t.Helper()
	for _, incident := range state.Incidents {
		if incident.Node == node && incident.Kind == kind && incident.Transaction == hash {
			return incident
		}
	}
	t.Fatalf("missing incident %s %s %s", node, kind, hash.Hex())
	return Incident{}
}

func TestHistoryRetainedServiceTransitions(t *testing.T) {
	config, first := serviceHistoryInput(t, "ipc-divergence", 1)
	path := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(path, config, 64*1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	state, err := history.Record(config, first)
	if err != nil {
		t.Fatal(err)
	}
	branch := findIncident(t, state, "", "branch_divergence", common.Hash{})
	config, again := serviceHistoryInput(t, "ipc-divergence", 2)
	state, err = history.Record(config, again)
	if err != nil {
		t.Fatal(err)
	}
	if duplicate := findIncident(t, state, "", "branch_divergence", common.Hash{}); duplicate.ID != branch.ID || duplicate.Occurrences != 1 || duplicate.FirstSequence != 1 || duplicate.LastSequence != 2 {
		t.Fatal("repeated observations did not deduplicate")
	}
	state, err = history.Review(Review{Action: "acknowledge", Incident: branch.ID, Reason: "Synthetic responder has inspected the fork."}, 2, again.FinishedUTC.Add(time.Second))
	if err != nil {
		t.Fatal(err)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	history, err = OpenHistory(path)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	state, err = history.Status()
	if err != nil || state.Sequence != 3 || findIncident(t, state, "", "branch_divergence", common.Hash{}).Status != "acknowledged" {
		t.Fatal("acknowledgement lost across reopen", err)
	}
	config, converged := serviceHistoryInput(t, "ipc-converged", 3)
	state, err = history.Record(config, converged)
	if err != nil {
		t.Fatal(err)
	}
	purchaseHash := first.Nodes[0].Tracked[1].Hash
	receipt := findIncident(t, state, "node-1", "receipt_change", purchaseHash)
	branch = findIncident(t, state, "", "branch_divergence", common.Hash{})
	if receipt.Status != "open" || receipt.FirstSequence != 4 || branch.Status != "acknowledged" || branch.Observation != "not_observed" {
		t.Fatal("convergence hid receipt loss or automatically resolved a review")
	}
	config, recovered := serviceHistoryInput(t, "ipc-divergence", 4)
	state, err = history.Record(config, recovered)
	if err != nil {
		t.Fatal(err)
	}
	receipt = findIncident(t, state, "node-1", "receipt_change", purchaseHash)
	if receipt.Status != "open" || receipt.Observation != "not_observed" {
		t.Fatal("one successful receipt must not automatically close recovery")
	}
	state, err = history.Review(Review{Action: "resolve", Incident: receipt.ID, Reason: "Synthetic operator review; acceptance evidence is external to this snapshot reducer."}, 5, recovered.FinishedUTC.Add(time.Second))
	if err != nil {
		t.Fatal(err)
	}
	config, unknown := serviceHistoryInput(t, "ipc-converged", 5)
	unknown.Nodes[0].Identity, unknown.Nodes[0].Consistency = "unknown", "unknown"
	unknown.Nodes[0].Head, unknown.Nodes[0].Tracked = nil, nil
	unknown.Nodes[0].Issues = []Issue{{Field: "endpoint", Code: "unavailable"}}
	state, err = history.Record(config, unknown)
	if err != nil {
		t.Fatal(err)
	}
	receipt = findIncident(t, state, "node-1", "receipt_change", purchaseHash)
	if receipt.Status != "resolved" || receipt.Observation != "unknown" {
		t.Fatal("lost coverage invented receipt loss or health")
	}
	config, rolledBack := serviceHistoryInput(t, "ipc-converged", 6)
	state, err = history.Record(config, rolledBack)
	if err != nil {
		t.Fatal(err)
	}
	reopened := findIncident(t, state, "node-1", "receipt_change", purchaseHash)
	if reopened.ID != receipt.ID || reopened.Status != "open" || reopened.Occurrences != 2 || reopened.LastReviewSequence != 6 || reopened.FirstSequence != 4 || reopened.LastSequence != 8 {
		t.Fatalf("receipt loss failed to reopen the same reviewed incident: %+v", reopened)
	}
	config, omitted := serviceHistoryInput(t, "ipc-converged", 7)
	config.Tracked = nil
	for i := range omitted.Nodes {
		omitted.Nodes[i].Tracked = nil
	}
	state, err = history.Record(config, omitted)
	if err != nil {
		t.Fatal(err)
	}
	if retained := findIncident(t, state, "node-1", "receipt_change", purchaseHash); retained.Status != "open" || retained.Observation != "unknown" {
		t.Fatal("removing tracking inputs erased an unresolved incident")
	}
	var exported bytes.Buffer
	if err := history.Export(&exported); err != nil {
		t.Fatal(err)
	}
	if bytes.Count(exported.Bytes(), []byte("\n")) != 10 || bytes.Contains(exported.Bytes(), []byte("Endpoint")) || !bytes.Contains(exported.Bytes(), []byte("canonical_native_success")) {
		t.Fatal("history export lost original observations or exposed endpoint configuration")
	}
	if directory := os.Getenv("FUSION_HISTORY_EVIDENCE"); directory != "" {
		if err := os.WriteFile(filepath.Join(directory, "timeline.jsonl"), exported.Bytes(), 0600); err != nil {
			t.Fatal(err)
		}
		raw, _ := json.MarshalIndent(state, "", "  ")
		if err := os.WriteFile(filepath.Join(directory, "timeline-status.json"), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	t.Log("nine durable events replay service evidence plus explicit retimed recurrence/unknown variants; acknowledgement survives reopen, success alone does not resolve, receipt loss reopens, omitted tracking stays unknown")
}

func TestHistoryScopeBudgetAndReviewGuards(t *testing.T) {
	config, report := serviceHistoryInput(t, "ipc-queued-gap", 1)
	path := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(path, config, 1024)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := history.Record(config, report); err == nil {
		t.Fatal("budget did not stop append")
	}
	state, err := history.Status()
	if err != nil || state.Sequence != 0 {
		t.Fatal("budget failure changed history", err)
	}
	if _, err := OpenHistory(path); err == nil {
		t.Fatal("concurrent opener was allowed")
	}
	if _, err := CreateHistory(path, config, 1024); err == nil {
		t.Fatal("existing directory reused")
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	path = filepath.Join(t.TempDir(), "history")
	history, err = CreateHistory(path, config, 1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	state, err = history.Record(config, report)
	if err != nil {
		t.Fatal(err)
	}
	state.Scope.Wallets["node-1"] = common.Address{}
	if err := history.CheckConfig(config); err != nil {
		t.Fatal("returned status aliased stored scope", err)
	}
	changed := config
	changed.NetworkID = "1"
	if _, err := history.Record(changed, report); err == nil {
		t.Fatal("different scope accepted")
	}
	if _, err := history.Record(config, report); err == nil {
		t.Fatal("older overlapping report accepted")
	}
	if _, err := history.Review(Review{Action: "resolve", Incident: state.Incidents[0].ID, Reason: "stale"}, 0, report.FinishedUTC.Add(time.Second)); err == nil {
		t.Fatal("stale review accepted")
	}
	if _, err := history.Review(Review{Action: "resolve", Incident: state.Incidents[0].ID}, 1, report.FinishedUTC.Add(time.Second)); err == nil {
		t.Fatal("unexplained review accepted")
	}
	after, err := history.Status()
	if err != nil || after.Sequence != state.Sequence || after.LogicalBytes != state.LogicalBytes {
		t.Fatal("rejected operation changed history", err)
	}
	other := filepath.Join(t.TempDir(), "ordinary-directory")
	if err := os.Mkdir(other, 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := OpenHistory(other); err == nil {
		t.Fatal("non-history directory opened")
	}
}

func TestHistoryCorruptionFailsClosed(t *testing.T) {
	for _, mode := range []string{"malformed", "sequence_gap", "metadata_missing"} {
		t.Run(mode, func(t *testing.T) {
			config, report := serviceHistoryInput(t, "ipc-divergence", 1)
			path := filepath.Join(t.TempDir(), "history")
			history, err := CreateHistory(path, config, 1024*1024)
			if err != nil {
				t.Fatal(err)
			}
			if _, err := history.Record(config, report); err != nil {
				t.Fatal(err)
			}
			original, err := history.db.Get([]byte("event/00000000000000000001"), nil)
			if err != nil {
				t.Fatal(err)
			}
			switch mode {
			case "malformed":
				err = history.db.Put([]byte("event/00000000000000000002"), []byte("{truncated"), &opt.WriteOptions{Sync: true})
			case "sequence_gap":
				err = history.db.Put([]byte("event/00000000000000000003"), original, &opt.WriteOptions{Sync: true})
			case "metadata_missing":
				err = history.db.Delete([]byte("metadata"), &opt.WriteOptions{Sync: true})
			}
			if err != nil {
				t.Fatal(err)
			}
			if _, err := history.Status(); err == nil {
				t.Fatal("corrupt history produced status")
			}
			if _, err := history.Record(config, report); err == nil {
				t.Fatal("corrupt history accepted append")
			}
			after, err := history.db.Get([]byte("event/00000000000000000001"), nil)
			if err != nil || !bytes.Equal(original, after) {
				t.Fatal("valid prefix changed", err)
			}
			if err := history.Close(); err != nil {
				t.Fatal(err)
			}
			if reopened, err := OpenHistory(path); err == nil {
				reopened.Close()
				t.Fatal("corrupt history silently recovered/reset")
			}
		})
	}
}

func TestHistoryAbruptProcessExit(t *testing.T) {
	config, report := serviceHistoryInput(t, "ipc-divergence", 1)
	if path := os.Getenv("FUSION_HISTORY_CHILD"); path != "" {
		history, err := OpenHistory(path)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := history.Record(config, report); err != nil {
			t.Fatal(err)
		}
		os.Exit(23)
	}
	path := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(path, config, 1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	command := exec.Command(os.Args[0], "-test.run=^TestHistoryAbruptProcessExit$", "-test.timeout=30s")
	command.Env = append(os.Environ(), "FUSION_HISTORY_CHILD="+path)
	output, err := command.CombinedOutput()
	if bytes.Contains(output, []byte("WARNING: DATA RACE")) {
		t.Fatal(string(output))
	}
	exit, ok := err.(*exec.ExitError)
	if !ok || exit.ExitCode() != 23 {
		t.Fatalf("child did not exit immediately after synced append: %v %s", err, output)
	}
	history, err = OpenHistory(path)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	state, err := history.Status()
	if err != nil || state.Sequence != 1 || len(state.Incidents) == 0 {
		t.Fatal("committed event lost after process exit", err)
	}
	var exported bytes.Buffer
	if err := history.Export(&exported); err != nil {
		t.Fatal(err)
	}
	if !bytes.Contains(exported.Bytes(), []byte(report.Nodes[0].Tracked[1].Hash.Hex())) {
		t.Fatal("original signed observation missing")
	}
	t.Log("sync-acknowledged observation survived process exit without database Close; this is not a power-loss test")
}
