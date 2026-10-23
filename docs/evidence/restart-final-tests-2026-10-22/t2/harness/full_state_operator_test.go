package restart

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestFullStateRecoveryOperator(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_OPERATOR_FULL_STATE_ROOT")
	if directory == "" {
		t.Skip("requires three fresh verified complete-state rehearsal copies")
	}
	if !filepath.IsAbs(directory) || !filepath.IsAbs(os.Getenv("FUSION_RECOVERY_OPERATOR")) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root, separately built command and no preserved backup environment required")
	}
	for _, role := range []string{"reference", "working", "verifier"} {
		path := filepath.Join(directory, role)
		requireFullStateCopy(t, path)
		prepareFullStateHandover(t, path)
		for _, file := range []string{"fixture.json", "handover.json"} {
			want, err := os.ReadFile(filepath.Join(directory, "reference", file))
			requireNoError(t, err)
			got, err := os.ReadFile(filepath.Join(path, file))
			requireNoError(t, err)
			if !bytes.Equal(got, want) {
				t.Fatal("complete-state substitutions differ from reference")
			}
		}
	}
	if !t.Run("reference", func(t *testing.T) {
		original, _, funding := openFullStateHandover(t, filepath.Join(directory, "reference"))
		successor := *original
		selectHandoverSuccessor(t, &successor, funding)
		writeOfflineRecoverySteps(t, directory, original, &successor, true)
	}) {
		t.Fatal("independent reference failed")
	}
	for stage := 1; stage <= 3; stage++ {
		var step offlineRecoveryStep
		readHandoverJSON(t, filepath.Join(directory, fmt.Sprintf("step-%d.json", stage)), &step)
		requireNoError(t, os.WriteFile(filepath.Join(directory, fmt.Sprintf("block-%02d.rlp", stage)), step.Expected, 0600))
		requireNoError(t, writeStateExportJSON(filepath.Join(directory, fmt.Sprintf("block-%02d.json", stage)), step.Ledger))
		t.Logf("reference stage=%d hash=%s root=%s tickets=%d changedAccounts=%d", stage, step.Ledger.Header.Hash().Hex(), step.Ledger.Header.Root.Hex(), len(step.Ledger.Tickets), len(step.Ledger.Differences))
	}
	auditFullStateHandover(t, filepath.Join(directory, "reference"), directory, 3)
	runRecoveryOperatorStages(t, directory, true)
}
