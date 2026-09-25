package restart

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestFullStateOfflineRecovery(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_OFFLINE_FULL_STATE_ROOT")
	if directory == "" {
		t.Skip("requires fresh verified complete-state rehearsal copies")
	}
	if !filepath.IsAbs(directory) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no preserved backup environment required")
	}
	reference := filepath.Join(directory, "reference")
	requireFullStateCopy(t, reference)
	prepareFullStateHandover(t, reference)
	original, _, funding := openFullStateHandover(t, reference)
	successor := *original
	selectHandoverSuccessor(t, &successor, funding)
	writeOfflineRecoverySteps(t, directory, original, &successor, true)
	for stage := 1; stage <= 3; stage++ {
		var step offlineRecoveryStep
		readHandoverJSON(t, filepath.Join(directory, fmt.Sprintf("step-%d.json", stage)), &step)
		requireNoError(t, os.WriteFile(filepath.Join(directory, fmt.Sprintf("block-%02d.rlp", stage)), step.Expected, 0600))
		requireNoError(t, writeStateExportJSON(filepath.Join(directory, fmt.Sprintf("block-%02d.json", stage)), step.Ledger))
		t.Logf("reference stage=%d hash=%s root=%s tickets=%d changedAccounts=%d", stage, step.Ledger.Header.Hash().Hex(), step.Ledger.Header.Root.Hex(), len(step.Ledger.Tickets), len(step.Ledger.Differences))
	}
	auditFullStateHandover(t, reference, directory, 3)
	for _, cut := range []string{"completion", "export", "import", "reservation", "signature"} {
		t.Run(cut, func(t *testing.T) {
			scenario := filepath.Join(directory, cut)
			prepareFullStateOfflineScenario(t, scenario, directory, cut)
			if cut == "reservation" || cut == "signature" {
				requireOfflineUncertain(t, scenario, cut)
				return
			}
			for stage := 1; stage <= 3; stage++ {
				chainPath := offlineChainPath(t, scenario, "working", true)
				before := offlineDatabaseFiles(t, chainPath)
				runOfflineRecoveryChild(t, scenario, stage, "sign", cut)
				if cut != "import" && !reflect.DeepEqual(before, offlineDatabaseFiles(t, chainPath)) {
					t.Fatal("complete-state offline operation changed chain files")
				}
				runOfflineRecoveryChild(t, scenario, stage, "recover", cut)
				runOfflineRecoveryChild(t, scenario, stage, "verify", cut)
				t.Logf("complete-state stage=%d kill-after=%s: exact artifact recovered; independent import and cold ledger agree", stage, cut)
			}
		})
	}
}

func prepareFullStateOfflineScenario(t *testing.T, scenario, reference, cut string) {
	t.Helper()
	roles := []string{"working", "verifier"}
	if cut == "reservation" || cut == "signature" {
		roles = roles[:1]
	}
	for _, role := range roles {
		path := filepath.Join(scenario, role)
		requireFullStateCopy(t, path)
		prepareFullStateHandover(t, path)
		for _, file := range []string{"fixture.json", "handover.json"} {
			want, err := os.ReadFile(filepath.Join(reference, "reference", file))
			requireNoError(t, err)
			got, err := os.ReadFile(filepath.Join(path, file))
			requireNoError(t, err)
			if !bytes.Equal(got, want) {
				t.Fatal("complete-state substitutions differ from reference")
			}
		}
	}
	for stage := 1; stage <= 3; stage++ {
		var step offlineRecoveryStep
		file := fmt.Sprintf("step-%d.json", stage)
		readHandoverJSON(t, filepath.Join(reference, file), &step)
		requireNoError(t, writeStateExportJSON(filepath.Join(scenario, file), step))
	}
	initializeOfflineJournals(t, scenario)
}
