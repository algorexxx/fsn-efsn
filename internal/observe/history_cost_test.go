package observe

import (
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"testing"
	"time"
)

type historyCostOperation struct {
	Name           string
	Nanoseconds    int64
	AllocatedBytes uint64
}

type historyCostSample struct {
	PriorReports    uint64
	FinalReports    uint64
	LogicalBytes    int64
	ClosedFileBytes int64
	ClosedFiles     int
	Operations      []historyCostOperation
}

func TestHistoryRetainedSnapshotCost(t *testing.T) {
	output := os.Getenv("FUSION_HISTORY_COST_EVIDENCE")
	if output == "" {
		t.Skip("requires an explicit new evidence file for bounded local history measurements")
	}
	if !filepath.IsAbs(output) {
		t.Fatal("absolute evidence file required")
	}
	config, report := serviceHistoryInput(t, "ipc-converged", 1)
	path := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(path, config, 64*1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if history != nil {
			history.Close()
		}
	})
	state, err := history.load()
	if err != nil {
		t.Fatal(err)
	}
	var samples []historyCostSample
	for _, count := range []uint64{10, 100, 1000} {
		for state.Sequence < count {
			next := retimeHistoryCostReport(report, state.Sequence+1)
			if _, err := history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: next.FinishedUTC, Report: &next}); err != nil {
				t.Fatal(err)
			}
		}
		sample := historyCostSample{PriorReports: count}
		expected := state.status()
		for repeat := 0; repeat < 3; repeat++ {
			var actual HistoryStatus
			sample.Operations = append(sample.Operations, measureHistoryCost(t, "status", func() error {
				actual, err = history.Status()
				return err
			}))
			if !reflect.DeepEqual(actual, expected) {
				t.Fatal("history replay changed retained status")
			}
		}
		next := retimeHistoryCostReport(report, count+1)
		sample.Operations = append(sample.Operations, measureHistoryCost(t, "append", func() error {
			expected, err = history.Record(config, next)
			return err
		}))
		if expected.Sequence != count+1 || expected.MaxBytes != 64*1024*1024 {
			t.Fatal("measured append did not retain its bounded history")
		}
		for repeat := 0; repeat < 3; repeat++ {
			sample.Operations = append(sample.Operations, measureHistoryCost(t, "export_discard", func() error { return history.Export(io.Discard) }))
		}
		for repeat := 0; repeat < 3; repeat++ {
			if err := history.Close(); err != nil {
				t.Fatal(err)
			}
			var actual HistoryStatus
			sample.Operations = append(sample.Operations, measureHistoryCost(t, "reopen_status", func() error {
				history, err = OpenHistory(path)
				if err != nil {
					return err
				}
				actual, err = history.Status()
				return err
			}))
			if !reflect.DeepEqual(actual, expected) {
				t.Fatal("reopening changed retained status")
			}
		}
		if err := history.Close(); err != nil {
			t.Fatal(err)
		}
		sample.FinalReports, sample.LogicalBytes = expected.Sequence, expected.LogicalBytes
		err := filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.Mode().IsRegular() {
				sample.ClosedFiles++
				sample.ClosedFileBytes += info.Size()
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
		samples = append(samples, sample)
		history, err = OpenHistory(path)
		if err != nil {
			t.Fatal(err)
		}
		state, err = history.load()
		if err != nil {
			t.Fatal(err)
		}
	}
	encoded, err := json.MarshalIndent(samples, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	file, err := os.OpenFile(output, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.Write(append(encoded, '\n')); err != nil {
		file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	t.Log("bounded local measurements complete; retained snapshot variants, no RPC acquisition or growing block ancestry")
}

func retimeHistoryCostReport(report Report, sequence uint64) Report {
	report.StartedUTC = time.Date(2026, 9, 27, 18, 0, 0, 0, time.UTC).Add(time.Duration(sequence) * 10 * time.Second)
	report.FinishedUTC = report.StartedUTC.Add(3 * time.Second)
	report.Nodes = append([]Observation(nil), report.Nodes...)
	for i := range report.Nodes {
		report.Nodes[i].StartedUTC = report.StartedUTC.Add(time.Second)
		report.Nodes[i].FinishedUTC = report.StartedUTC.Add(2 * time.Second)
	}
	return report
}

func measureHistoryCost(t *testing.T, name string, action func() error) historyCostOperation {
	t.Helper()
	runtime.GC()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	started := time.Now()
	err := action()
	elapsed := time.Since(started)
	runtime.ReadMemStats(&after)
	if err != nil {
		t.Fatal(err)
	}
	return historyCostOperation{Name: name, Nanoseconds: elapsed.Nanoseconds(), AllocatedBytes: after.TotalAlloc - before.TotalAlloc}
}
