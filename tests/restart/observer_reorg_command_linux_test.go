package restart

import (
	"bytes"
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

type observerReorgCommand struct {
	command *exec.Cmd
	stdout  bytes.Buffer
	stderr  bytes.Buffer
	before  [2]nodeRehearsalStatus
	started time.Time
}

func startObserverReorgCommand(t *testing.T, binary string, nodes [2]*rehearsalNode, args ...string) *observerReorgCommand {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	result := &observerReorgCommand{command: exec.CommandContext(ctx, binary, args...), before: [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}, started: time.Now().UTC()}
	for _, status := range result.before {
		if !status.Mining || !status.AutoBuy {
			t.Fatal("both ordinary miners must remain enabled before live collection")
		}
	}
	result.command.Stdout, result.command.Stderr = &result.stdout, &result.stderr
	t.Cleanup(func() {
		cancel()
		if result.command.Process != nil && result.command.ProcessState == nil {
			_ = result.command.Wait()
		}
	})
	requireNoError(t, result.command.Start())
	return result
}

func finishObserverReorgCommand(t *testing.T, command *observerReorgCommand, output, name string, nodes [2]*rehearsalNode) []byte {
	t.Helper()
	err := command.command.Wait()
	requireNoError(t, os.WriteFile(filepath.Join(output, name+".json"), command.stdout.Bytes(), 0600))
	requireNoError(t, os.WriteFile(filepath.Join(output, name+"-stderr.txt"), command.stderr.Bytes(), 0600))
	after := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, name+"-command.json"), map[string]interface{}{"StartedUTC": command.started, "FinishedUTC": time.Now().UTC(), "Before": command.before, "After": after}))
	if err != nil || command.stderr.Len() != 0 {
		t.Fatalf("live observer exit=%v stderr=%s", err, command.stderr.Bytes())
	}
	for i, status := range after {
		if !status.AutoBuy || status.Signatures < command.before[i].Signatures {
			t.Fatal("live collector changed automatic buying or signature history")
		}
	}
	return command.stdout.Bytes()
}
