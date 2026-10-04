package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

type historyCheckCommand struct {
	Args       []string
	Exit       int
	Output     string
	Diagnostic string
}

func TestCommandHistoryCheck(t *testing.T) {
	for _, mode := range []string{"in-process", "binary"} {
		t.Run(mode, func(t *testing.T) {
			binary := ""
			if mode == "binary" {
				binary = os.Getenv("FUSION_OBSERVER_CHECK_BINARY")
				if binary == "" {
					t.Skip("requires an explicit observer binary for process exit checks")
				}
				if !filepath.IsAbs(binary) {
					t.Fatal("observer binary must be absolute")
				}
			}
			checkCommandLifecycle(t, mode, binary)
		})
	}
}

func checkCommandLifecycle(t *testing.T, mode, binary string) {
	t.Helper()
	config := observe.Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash("0x1"), AnchorNumber: 1, AnchorHash: common.HexToHash("0x2"), Nodes: []observe.NodeConfig{{Name: "retired-fixture", Role: "retired", Wallet: common.HexToAddress("0x1"), Endpoint: "http://127.0.0.1:1"}}}
	path := filepath.Join(t.TempDir(), "history")
	history, err := observe.CreateHistory(path, config, 65536)
	if err != nil {
		t.Fatal(err)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	args := []string{"--history", path, "--history-check", "--report-max-age", "1h", "--history-min-free", "1"}
	var records []historyCheckCommand
	invoke := func(arguments ...string) historyCheckCommand {
		result := invokeHistoryCheck(t, binary, arguments)
		records = append(records, result)
		return result
	}
	assertHistoryCheck(t, invoke(args...), 1, []string{"collection_missing"})
	if result := invoke("--history", path, "--history-status"); result.Exit != 0 {
		t.Fatal("legacy status became a health check")
	}
	history, err = observe.OpenHistory(path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { history.Close() })
	if result := invoke(args...); result.Exit != 1 || len(result.Output) != 0 {
		t.Fatal("locked history appeared checked", result)
	}
	now := time.Now().UTC()
	report, err := observe.Collect(context.Background(), config, time.Second, func() time.Time { return now })
	if err != nil {
		t.Fatal(err)
	}
	if _, err := history.Record(config, report); err != nil {
		t.Fatal(err)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	before := invoke("--history", path, "--history-export").Output
	assertHistoryCheck(t, invoke(args...), 0, []string{})
	assertHistoryCheck(t, invoke(append(append([]string{}, args...), "--report-max-age", "1ns")...), 1, []string{"collection_stale"})
	assertHistoryCheck(t, invoke(append(append([]string{}, args...), "--history-min-free", "65536")...), 1, []string{"history_headroom_low"})
	for _, extra := range [][]string{
		{"--report-max-age", "0s"}, {"--report-max-age", "-1s"}, {"--history-min-free", "0"}, {"--history-min-free", "65537"},
		{"--history-check=false"}, {"--config", "missing.json"}, {"--timeout", "1s"},
		{"--history-status"}, {"--history-export"}, {"--init-history"},
		{"--history-copy", filepath.Join(filepath.Dir(path), "unused"), "--history-budget", "131072", "--at-sequence", "1"},
		{"--history-action", "acknowledge", "--incident", "unused", "--at-sequence", "1", "--reason", "unused"},
		{"--backfill-node", "retired-fixture", "--backfill-blocks", "1"},
		{"--anchor-inventory", "retired-fixture"}, {"--ticket-timeline", "retired-fixture", "--ticket-blocks", "1"},
	} {
		result := invoke(append(append([]string{}, args...), extra...)...)
		if result.Exit != 1 || len(result.Output) != 0 {
			t.Fatal("invalid flags appeared checked", result)
		}
	}
	if result := invoke("--history", filepath.Join(filepath.Dir(path), "absent"), "--history-check", "--report-max-age", "1h", "--history-min-free", "1"); result.Exit != 1 || len(result.Output) != 0 {
		t.Fatal("absent history appeared checked", result)
	}
	if mode == "in-process" {
		reader, writer := io.Pipe()
		reader.Close()
		defer writer.Close()
		if err := run(context.Background(), args, writer, io.Discard); !errors.Is(err, io.ErrClosedPipe) {
			t.Fatal("output failure was hidden", err)
		}
	}
	if after := invoke("--history", path, "--history-export"); after.Exit != 0 || before != after.Output {
		t.Fatal("checks changed retained history")
	}
	if directory := os.Getenv("FUSION_HISTORY_CHECK_EVIDENCE"); directory != "" {
		if !filepath.IsAbs(directory) {
			t.Fatal("absolute evidence directory required")
		}
		file, err := os.OpenFile(filepath.Join(directory, "commands-"+mode+".json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			t.Fatal(err)
		}
		defer file.Close()
		if err := json.NewEncoder(file).Encode(records); err != nil {
			t.Fatal(err)
		}
	}
}

func invokeHistoryCheck(t *testing.T, binary string, args []string) historyCheckCommand {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	var output, diagnostic bytes.Buffer
	result := historyCheckCommand{Args: args}
	if binary == "" {
		if err := run(ctx, args, &output, &diagnostic); err != nil {
			result.Exit = 1
			diagnostic.WriteString(err.Error())
		}
	} else {
		command := exec.CommandContext(ctx, binary, args...)
		command.Stdout, command.Stderr = &output, &diagnostic
		if err := command.Run(); err != nil {
			var failed *exec.ExitError
			if !errors.As(err, &failed) {
				t.Fatal(err)
			}
			result.Exit = failed.ExitCode()
		}
	}
	result.Output, result.Diagnostic = output.String(), diagnostic.String()
	return result
}

func assertHistoryCheck(t *testing.T, command historyCheckCommand, exit int, problems []string) {
	t.Helper()
	var check observe.HistoryCheck
	if err := json.Unmarshal([]byte(command.Output), &check); err != nil || command.Exit != exit || !reflect.DeepEqual(check.Problems, problems) || check.Version != 1 {
		t.Fatal("unexpected command check", command, check, err)
	}
}
