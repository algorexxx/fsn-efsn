package observe

import (
	"bytes"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
)

type historyOpenFixture struct {
	history *History
	path    string
	config  Config
	report  Report
	status  HistoryStatus
	export  []byte
}

func reopenHistoryFixture(t *testing.T) *historyOpenFixture {
	t.Helper()
	config, report := serviceHistoryInput(t, "ipc-divergence", 1)
	path := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(path, config, 64*1024)
	if err != nil {
		t.Fatal(err)
	}
	fixture := &historyOpenFixture{history: history, path: path, config: config, report: report}
	t.Cleanup(func() {
		if fixture.history != nil {
			fixture.history.Close()
		}
	})
	fixture.status, err = history.Record(config, report)
	if err != nil {
		t.Fatal(err)
	}
	var original bytes.Buffer
	if err := history.Export(&original); err != nil {
		t.Fatal(err)
	}
	fixture.export = original.Bytes()
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	fixture.history, err = OpenHistory(path)
	if err != nil {
		t.Fatal(err)
	}
	return fixture
}

func TestHistoryFirstOperationRejectionPreservesEvidence(t *testing.T) {
	for _, mode := range []string{"budget", "old_report", "wrong_scope", "stale_review"} {
		t.Run(mode, func(t *testing.T) {
			fixture := reopenHistoryFixture(t)
			config, report := serviceHistoryInput(t, "ipc-divergence", 2)
			var err error
			switch mode {
			case "budget":
				report.Limitations = []string{strings.Repeat("bounded", 10000)}
				_, err = fixture.history.Record(config, report)
			case "old_report":
				_, err = fixture.history.Record(config, fixture.report)
			case "wrong_scope":
				config.NetworkID = "999999"
				_, err = fixture.history.Record(config, report)
			case "stale_review":
				incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
				_, err = fixture.history.Review(Review{Action: "acknowledge", Incident: incident.ID, Reason: "stale review must fail"}, 2, fixture.report.FinishedUTC.Add(time.Second))
			}
			if err == nil {
				t.Fatal("invalid first operation succeeded")
			}
			actual, err := fixture.history.Status()
			if err != nil || !reflect.DeepEqual(actual, fixture.status) {
				t.Fatal("rejected first operation changed retained state", err)
			}
			var exported bytes.Buffer
			if err := fixture.history.Export(&exported); err != nil || !bytes.Equal(exported.Bytes(), fixture.export) {
				t.Fatal("rejected first operation changed original evidence", err)
			}
		})
	}
}

func TestHistoryOpenedStatusDoesNotAliasLaterReads(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	first, err := fixture.history.Status()
	if err != nil {
		t.Fatal(err)
	}
	first.Scope.Wallets["node-1"] = common.Address{}
	first.Limitations[0] = "caller changed this returned slice"
	for i := range first.Incidents {
		first.Incidents[i].Status = "resolved"
		if len(first.Incidents[i].Details) > 0 {
			first.Incidents[i].Details[0] = "caller changed returned details"
		}
	}
	after, err := fixture.history.Status()
	if err != nil || !reflect.DeepEqual(after, fixture.status) {
		t.Fatal("returned first status changed subsequent replay", err)
	}
	incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
	review := Review{Action: "acknowledge", Incident: incident.ID, Reason: "valid review after caller mutation"}
	updated, err := fixture.history.Review(review, 1, fixture.report.FinishedUTC.Add(time.Second))
	if err != nil || updated.Sequence != 2 || findIncident(t, updated, "", "branch_divergence", common.Hash{}).Status != "acknowledged" {
		t.Fatal("caller mutation interfered with a subsequent valid write", err)
	}
}

func TestHistoryClosedBeforeFirstOperationRejectsAccess(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	if err := fixture.history.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.history.Status(); err == nil {
		t.Fatal("closed handle returned its opening status")
	}
	var exported bytes.Buffer
	if err := fixture.history.Export(&exported); err == nil || exported.Len() != 0 {
		t.Fatal("closed handle exported history")
	}
	config, report := serviceHistoryInput(t, "ipc-divergence", 2)
	if _, err := fixture.history.Record(config, report); err == nil {
		t.Fatal("closed handle accepted a write")
	}
}

func TestHistoryConcurrentFirstReviewsKeepSequenceGuard(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
	ready := make(chan struct{})
	results := make(chan error, 2)
	for _, reason := range []string{"first reviewer", "second reviewer"} {
		review := Review{Action: "acknowledge", Incident: incident.ID, Reason: reason}
		go func(review Review) {
			<-ready
			_, err := fixture.history.Review(review, 1, fixture.report.FinishedUTC.Add(time.Second))
			results <- err
		}(review)
	}
	close(ready)
	first, second := <-results, <-results
	if (first == nil) == (second == nil) {
		t.Fatal("exactly one concurrent review must commit", first, second)
	}
	status, err := fixture.history.Status()
	if err != nil || status.Sequence != 2 || findIncident(t, status, "", "branch_divergence", common.Hash{}).LastReviewSequence != 2 {
		t.Fatal("concurrent first reviews bypassed the sequence guard", err)
	}
	var exported bytes.Buffer
	if err := fixture.history.Export(&exported); err != nil || !bytes.HasPrefix(exported.Bytes(), fixture.export) {
		t.Fatal("concurrent review rewrote earlier evidence", err)
	}
}

func TestHistoryFirstWriteFailureDoesNotRetainUncommittedState(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
	if err := fixture.history.db.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.history.Review(Review{Action: "acknowledge", Incident: incident.ID, Reason: "failed storage must not commit this review"}, 1, fixture.report.FinishedUTC.Add(time.Second)); err == nil {
		t.Fatal("closed storage accepted a review")
	}
	if _, err := fixture.history.Status(); err == nil {
		t.Fatal("failed storage returned uncommitted in-memory status")
	}
	var err error
	fixture.history, err = OpenHistory(fixture.path)
	if err != nil {
		t.Fatal(err)
	}
	status, err := fixture.history.Status()
	if err != nil || !reflect.DeepEqual(status, fixture.status) {
		t.Fatal("failed write changed durable review state", err)
	}
}
