package observe

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
)

func TestHistoryCopyResumesExhaustedEvidence(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	incident := findIncident(t, fixture.status, "", "branch_divergence", common.Hash{})
	status, err := fixture.history.Review(Review{Action: "acknowledge", Incident: incident.ID, Reason: "Retain unresolved fixture incident."}, 1, fixture.report.FinishedUTC.Add(time.Second))
	if err != nil {
		t.Fatal(err)
	}
	before := exportBacklog(t, fixture.history)
	config, next := serviceHistoryInput(t, "ipc-divergence", 2)
	next.Limitations = []string{strings.Repeat("x", 32768)}
	if _, err := fixture.history.Record(config, next); err == nil {
		t.Fatal("fixture must reach its original 64 KiB budget")
	}
	destination := filepath.Join(t.TempDir(), "larger")
	expected := status
	expected.MaxBytes, expected.LogicalBytes = 131072, status.LogicalBytes+1

	copied, err := fixture.history.CopyWithBudget(context.Background(), destination, 131072, 2)

	if err != nil || !reflect.DeepEqual(copied, expected) {
		t.Fatal("capacity copy changed original status beyond budget digit growth", err)
	}
	assertCopiedHistoryContinuation(t, fixture, destination, config, next, before, expected, incident.ID)
}

func assertCopiedHistoryContinuation(t *testing.T, fixture *historyOpenFixture, destination string, config Config, next Report, before []byte, expected HistoryStatus, incidentID string) {
	t.Helper()
	copied, err := OpenHistory(destination)
	if err != nil {
		t.Fatal(err)
	}
	defer copied.Close()
	status, err := copied.Status()
	if err != nil || !reflect.DeepEqual(status, expected) {
		t.Fatal("copy did not reopen at the same reviewed sequence", err)
	}
	after := exportBacklog(t, copied)
	if !bytes.Equal(bytes.SplitN(before, []byte{'\n'}, 2)[1], bytes.SplitN(after, []byte{'\n'}, 2)[1]) {
		t.Fatal("copy changed original event bytes")
	}
	status, err = copied.Record(config, next)
	if err != nil || status.Sequence != 3 || findIncident(t, status, "", "branch_divergence", common.Hash{}).ID != incidentID || findIncident(t, status, "", "branch_divergence", common.Hash{}).Status != "acknowledged" {
		t.Fatal("new history did not continue the unresolved incident", err)
	}
	if _, err := fixture.history.Record(config, next); err == nil || !bytes.Equal(before, exportBacklog(t, fixture.history)) {
		t.Fatal("copy enlarged or changed the source")
	}
}

func TestHistoryCopyPreservesTicketBaseline(t *testing.T) {
	config, events := miningTicketFixture(t)
	history, _ := ticketHistory(t, config, events)
	status, err := history.Status()
	if err != nil {
		t.Fatal(err)
	}
	expected := make([]TicketTimeline, len(config.Nodes))
	for i, node := range config.Nodes {
		expected[i], err = history.TicketTimeline(node.Name, 0, 128)
		if err != nil || !reflect.DeepEqual(expected[i].Inventory, expectedTicketInventory(t, 29, node.Wallet)) {
			t.Fatal("fixture differs from independent executed wallet ledger", err)
		}
	}
	destination := filepath.Join(t.TempDir(), "copied")

	_, err = history.CopyWithBudget(context.Background(), destination, 33554432, status.Sequence)

	if err != nil {
		t.Fatal(err)
	}
	copied, err := OpenHistory(destination)
	if err != nil {
		t.Fatal(err)
	}
	defer copied.Close()
	for i, node := range config.Nodes {
		actual, err := copied.TicketTimeline(node.Name, 0, 128)
		if err != nil || !reflect.DeepEqual(actual, expected[i]) {
			t.Fatal("copy lost original baseline or native ticket events", err)
		}
	}
}

func TestHistoryCopyRejectsUnsafeInputs(t *testing.T) {
	for _, mode := range []string{"stale", "missing_sequence", "same_budget", "smaller_budget", "oversized_budget", "relative", "nested", "existing", "missing_parent", "cancelled"} {
		t.Run(mode, func(t *testing.T) {
			fixture := reopenHistoryFixture(t)
			destination := filepath.Join(t.TempDir(), "copy")
			budget, sequence := int64(131072), uint64(1)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			switch mode {
			case "stale":
				sequence = 2
			case "missing_sequence":
				sequence = 0
			case "same_budget":
				budget = 65536
			case "smaller_budget":
				budget = 32768
			case "oversized_budget":
				budget = 1073741825
			case "relative":
				destination = "relative-copy"
			case "nested":
				destination = filepath.Join(fixture.path, "copy")
			case "existing":
				if err := os.Mkdir(destination, 0700); err != nil {
					t.Fatal(err)
				}
			case "missing_parent":
				destination = filepath.Join(destination, "missing", "copy")
			case "cancelled":
				cancel()
			}

			_, err := fixture.history.CopyWithBudget(ctx, destination, budget, sequence)

			if err == nil || !bytes.Equal(fixture.export, exportBacklog(t, fixture.history)) {
				t.Fatal("invalid copy succeeded or changed source", mode, err)
			}
			if _, err := os.Stat(filepath.Join(destination, "FORMAT")); !os.IsNotExist(err) {
				t.Fatal("rejected input published a history", err)
			}
		})
	}
}

type interruptedHistoryCopy struct {
	context.Context
	checks int
}

func (ctx *interruptedHistoryCopy) Err() error {
	ctx.checks++
	if ctx.checks >= 3 {
		return context.Canceled
	}
	return nil
}

func TestHistoryCopyRejectsSourceAlias(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	alias := filepath.Join(t.TempDir(), "source-alias")
	if err := os.Symlink(fixture.path, alias); err != nil {
		t.Skip("directory symlinks unavailable", err)
	}
	destination := filepath.Join(alias, "copy")

	_, err := fixture.history.CopyWithBudget(context.Background(), destination, 131072, 1)

	if err == nil || !bytes.Equal(fixture.export, exportBacklog(t, fixture.history)) {
		t.Fatal("aliased source destination accepted or source changed", err)
	}
	if _, err := os.Stat(destination); !os.IsNotExist(err) {
		t.Fatal("copy created a directory inside aliased source", err)
	}
}

func TestHistoryCopyInterruptedDestinationCannotOpen(t *testing.T) {
	fixture := reopenHistoryFixture(t)
	config, report := serviceHistoryInput(t, "ipc-divergence", 2)
	if _, err := fixture.history.Record(config, report); err != nil {
		t.Fatal(err)
	}
	before := exportBacklog(t, fixture.history)
	destination := filepath.Join(t.TempDir(), "interrupted")
	ctx := &interruptedHistoryCopy{Context: context.Background()}

	_, err := fixture.history.CopyWithBudget(ctx, destination, 131072, 2)

	if err != context.Canceled || !bytes.Equal(before, exportBacklog(t, fixture.history)) {
		t.Fatal("interruption changed original history", err)
	}
	if marker, err := os.ReadFile(filepath.Join(destination, "COPYING")); err != nil || string(marker) != historyFormat {
		t.Fatal("partial output did not retain incomplete marker", err)
	}
	if opened, err := OpenHistory(destination); err == nil {
		opened.Close()
		t.Fatal("partially copied history was opened as complete")
	}
	if _, err := fixture.history.CopyWithBudget(context.Background(), destination, 131072, 2); err == nil {
		t.Fatal("retry overwrote a partial destination")
	}
}
