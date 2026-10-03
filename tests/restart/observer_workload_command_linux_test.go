package restart

import (
	"bytes"
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"testing"
	"time"
)

type observerWorkloadCommand struct {
	Name        string
	Nanoseconds int64
	ExitCode    int
	Before      []nodeRehearsalStatus
	After       []nodeRehearsalStatus
	raw         []byte
}

func runObserverWorkloadCommand(t *testing.T, binary, output, name string, nodes [2]*rehearsalNode, producer int, allowBudgetFailure bool, args ...string) observerWorkloadCommand {
	t.Helper()
	result := observerWorkloadCommand{Name: name}
	for _, node := range nodes {
		if node != nil {
			result.Before = append(result.Before, node.status(t))
		}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, binary, args...)
	var stdout, stderr bytes.Buffer
	command.Stdout, command.Stderr = &stdout, &stderr
	started := time.Now()
	err := command.Run()
	result.Nanoseconds = time.Since(started).Nanoseconds()
	if command.ProcessState != nil {
		result.ExitCode = command.ProcessState.ExitCode()
	} else {
		result.ExitCode = -1
	}
	result.raw = stdout.Bytes()
	requireNoError(t, os.WriteFile(filepath.Join(output, name+".json"), result.raw, 0600))
	requireNoError(t, os.WriteFile(filepath.Join(output, name+"-stderr.txt"), stderr.Bytes(), 0600))
	for _, node := range nodes {
		if node != nil {
			result.After = append(result.After, node.status(t))
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, name+"-command.json"), result))
	if err != nil {
		if !allowBudgetFailure || result.ExitCode != 1 || stdout.Len() != 0 || stderr.String() != "history byte budget exhausted; evidence retained without pruning\n" {
			t.Fatalf("observer command %s failed: %v stderr=%s", name, err, stderr.Bytes())
		}
	} else if stderr.Len() != 0 {
		t.Fatalf("observer command %s emitted diagnostics: %s", name, stderr.Bytes())
	}
	for i, before := range result.Before {
		after := result.After[i]
		mining := i == producer
		if before.Mining != mining || before.AutoBuy != mining || after.Mining != mining || after.AutoBuy != mining || after.Number < before.Number || after.Signatures < before.Signatures {
			t.Fatal("observer command changed mining controls or one-producer progression")
		}
	}
	if producer < 0 && !reflect.DeepEqual(result.Before, result.After) {
		t.Fatal("observer command changed stopped-node state")
	}
	return result
}
