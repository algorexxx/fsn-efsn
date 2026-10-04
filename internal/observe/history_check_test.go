package observe

import (
	"bytes"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
)

func TestHistoryCheckBoundariesAndUnresolvedState(t *testing.T) {
	now := time.Date(2026, 10, 4, 12, 0, 0, 0, time.UTC)
	for _, test := range []struct {
		name     string
		change   func(*HistoryStatus)
		problems []string
	}{
		{"fresh_at_headroom_boundary", func(s *HistoryStatus) {}, []string{}},
		{"missing_collection", func(s *HistoryStatus) { s.LastReportUTC = time.Time{} }, []string{"collection_missing"}},
		{"expiry_boundary", func(s *HistoryStatus) { s.LastReportUTC = now.Add(-time.Minute) }, []string{"collection_stale"}},
		{"recent_event_old_collection", func(s *HistoryStatus) { s.LastReportUTC = now.Add(-time.Hour) }, []string{"collection_stale"}},
		{"future_event", func(s *HistoryStatus) { s.LastEventUTC = now.Add(time.Nanosecond) }, []string{"history_time_in_future"}},
		{"future_collection", func(s *HistoryStatus) { s.LastReportUTC = now.Add(time.Nanosecond) }, []string{"history_time_in_future"}},
		{"low_headroom", func(s *HistoryStatus) { s.LogicalBytes = 3073 }, []string{"history_headroom_low"}},
		{"open", func(s *HistoryStatus) {
			s.Incidents = []Incident{{ID: "retained", Status: "open", Observation: "present"}}
		}, []string{"unresolved_incidents"}},
		{"acknowledged_not_observed", func(s *HistoryStatus) {
			s.Incidents = []Incident{{ID: "retained", Status: "acknowledged", Observation: "not_observed"}}
		}, []string{"unresolved_incidents"}},
		{"acknowledged_unknown", func(s *HistoryStatus) {
			s.Incidents = []Incident{{ID: "retained", Status: "acknowledged", Observation: "unknown"}}
		}, []string{"unresolved_incidents"}},
		{"resolved", func(s *HistoryStatus) {
			s.Incidents = []Incident{{ID: "retained", Status: "resolved", Observation: "not_observed"}}
		}, []string{}},
	} {
		t.Run(test.name, func(t *testing.T) {
			status := HistoryStatus{Version: 1, Sequence: 2, LastReportUTC: now.Add(-59 * time.Second), LastEventUTC: now, MaxBytes: 4096, LogicalBytes: 3072}
			test.change(&status)
			expected := HistoryCheck{Version: 1, CheckedUTC: now, MaxReportAge: "1m0s", MinFreeBytes: 1024, Problems: test.problems, History: status}

			actual, err := CheckHistory(status, now, time.Minute, 1024)

			if err != nil || !reflect.DeepEqual(actual, expected) {
				t.Fatal("unexpected check", actual, err)
			}
		})
	}
}

func TestHistoryCheckRequiresExplicitBounds(t *testing.T) {
	now := time.Date(2026, 10, 4, 12, 0, 0, 0, time.UTC)
	for _, test := range []struct {
		when time.Time
		age  time.Duration
		free int64
	}{{time.Time{}, time.Minute, 1}, {now, 0, 1}, {now, -time.Second, 1}, {now, time.Minute, 0}, {now, time.Minute, -1}, {now, time.Minute, 4097}} {
		_, err := CheckHistory(HistoryStatus{Version: 1, MaxBytes: 4096}, test.when, test.age, test.free)

		if err == nil {
			t.Fatal("invalid check bounds accepted", test)
		}
	}
}

func TestHistoryCheckFailedAppendAndReviewCannotRenewCollection(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	config, failed := serviceHistoryInput(t, "ipc-divergence", 10)
	failed.Limitations = []string{strings.Repeat("x", 65536)}
	if _, err := fixture.history.Record(config, failed); err == nil {
		t.Fatal("oversized collection unexpectedly committed")
	}
	incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
	now := time.Date(2026, 9, 27, 18, 2, 0, 0, time.UTC)
	status, err := fixture.history.Review(Review{Action: "acknowledge", Incident: incident.ID, Reason: "Fixture review after collection failure."}, 1, now)
	if err != nil {
		t.Fatal(err)
	}
	before := exportBacklog(t, fixture.history)
	expectedTime := time.Date(2026, 9, 27, 18, 0, 13, 0, time.UTC)
	expectedProblems := []string{"collection_stale", "history_headroom_low", "unresolved_incidents"}

	actual, err := CheckHistory(status, now, time.Minute, 65536)

	if err != nil || !reflect.DeepEqual(actual.Problems, expectedProblems) || actual.History.Sequence != 2 || !actual.History.LastReportUTC.Equal(expectedTime) {
		t.Fatal("failed collection or fresh review hid loss of collection", actual, err)
	}
	if !bytes.Equal(before, exportBacklog(t, fixture.history)) {
		t.Fatal("check changed retained history")
	}
}
