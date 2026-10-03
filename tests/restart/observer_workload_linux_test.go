package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func TestObserverMixedWorkloadBudget(t *testing.T) {
	output, binary := os.Getenv("FUSION_RESTART_OBSERVER_WORKLOAD_RESULTS"), os.Getenv("FUSION_RESTART_OBSERVER_BIN")
	if output == "" || binary == "" {
		t.Skip("requires an explicitly built observer and isolated mixed-workload evidence directory")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(output) || !filepath.IsAbs(binary) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute observer/evidence paths, isolated rehearsal and no backup input required")
	}
	requireNoError(t, os.Mkdir(output, 0700))
	pair := seedDenseMinerPair(t)
	anchor := pair.miners[0].chain.CurrentBlock()
	producer := 0
	if preferredFixtureProducer(t, pair.miners[0], pair.miners[1]) == pair.miners[0] {
		producer = 1
	}
	truth := [2]observerServiceTruth{captureObserverTruth(t, pair.miners[0], pair.miners[0].owner), captureObserverTruth(t, pair.miners[1], pair.miners[1].owner)}
	config := observe.Config{ChainID: pair.genesis.Config.ChainID.String(), NetworkID: "99032659", Genesis: pair.miners[0].chain.Genesis().Hash(), AnchorNumber: anchor.NumberU64(), AnchorHash: anchor.Hash()}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "genesis.json"), pair.genesis))
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "anchor-truth.json"), truth))
	closeDenseMinerPair(t, pair)
	for i, path := range pair.paths {
		var lab nodeRehearsalConfig
		readHandoverJSON(t, filepath.Join(path, "lab.json"), &lab)
		lab.HTTP = true
		requireNoError(t, os.WriteFile(filepath.Join(path, "lab.json"), mustObserverJSON(t, lab), 0600))
		config.Nodes = append(config.Nodes, observe.NodeConfig{Name: fmt.Sprintf("node-%d", i+1), Endpoint: filepath.Join(path, "lab.ipc"), Wallet: pair.miners[i].owner, Role: "maintenance"})
	}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, pair.paths[0], 8*time.Minute), startRehearsalNodeWithTimeout(t, pair.paths[1], 8*time.Minute)}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	maintenance := filepath.Join(output, "maintenance-config.json")
	requireNoError(t, writeStateExportJSON(maintenance, config))
	history := filepath.Join(t.TempDir(), "history")
	activeProducer := -1
	var commands []observerWorkloadCommand
	invoke := func(name string, allowFailure bool, args ...string) observerWorkloadCommand {
		result := runObserverWorkloadCommand(t, binary, output, name, nodes, activeProducer, allowFailure, args...)
		commands = append(commands, result)
		return result
	}
	invoke("init", false, "--config", maintenance, "--history", history, "--init-history", "--history-budget", "524288")
	for i, node := range config.Nodes {
		result := invoke(node.Name+"-anchor", false, "--config", maintenance, "--history", history, "--timeout", "5s", "--anchor-inventory", node.Name)
		var inventory observe.AnchorInventory
		requireNoError(t, json.Unmarshal(result.raw, &inventory))
		if inventory.Status != "ready" || !reflect.DeepEqual(inventory.Tickets, truth[i].Tickets) {
			t.Fatal("pre-production baseline differs from independent anchor state")
		}
	}
	initialExport := invoke("anchor-export", false, "--history", history, "--history-export").raw
	for i := range config.Nodes {
		config.Nodes[i].Role = "verifier"
		if i == producer {
			config.Nodes[i].Role = "producer"
		}
	}
	ipcPath, httpPath := filepath.Join(output, "ipc-config.json"), filepath.Join(output, "http-config.json")
	requireNoError(t, writeStateExportJSON(ipcPath, config))
	httpConfig := config
	httpConfig.Nodes = append([]observe.NodeConfig(nil), config.Nodes...)
	for i, node := range nodes {
		endpoint, err := os.ReadFile(filepath.Join(node.path, "http.endpoint"))
		requireNoError(t, err)
		httpConfig.Nodes[i].Endpoint = string(endpoint)
	}
	requireNoError(t, writeStateExportJSON(httpPath, httpConfig))
	startCompetingMiner(t, nodes[producer])
	activeProducer = producer
	lastHeight := anchor.NumberU64()
	for round := 0; round < 6; round++ {
		awaitRehearsal(t, 90*time.Second, func() bool { return nodes[0].status(t).Number > lastHeight && nodes[1].status(t).Number > lastHeight })
		path, transport := ipcPath, "ipc"
		if round%2 == 1 {
			path, transport = httpPath, "http"
		}
		name := fmt.Sprintf("round-%d-%s", round+1, transport)
		result := invoke(name+"-snapshot", false, "--config", path, "--history", history, "--timeout", "5s")
		var report observe.Report
		requireNoError(t, json.Unmarshal(result.raw, &report))
		for _, node := range report.Nodes {
			if node.Identity != "matches" || node.Consistency != "stable" || !node.TicketsKnown || node.Head == nil {
				t.Fatal("ordinary snapshot did not retain a stable inventory")
			}
		}
		nextHeight := lastHeight
		for _, node := range config.Nodes {
			result = invoke(name+"-"+node.Name+"-backfill", false, "--config", path, "--history", history, "--timeout", "5s", "--backfill-node", node.Name, "--backfill-blocks", "128")
			coverage := requireMiningCoverage(t, result.raw, node.Name, "complete_at_observation")
			if coverage.StoredThrough.Number <= lastHeight {
				t.Fatal("mixed collection did not advance block coverage")
			}
			if coverage.StoredThrough.Number > nextHeight {
				nextHeight = coverage.StoredThrough.Number
			}
		}
		lastHeight = nextHeight
	}
	stopPeerAutoMiner(t, nodes[producer])
	activeProducer = -1
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	left, right := readObserverReorgInventory(t, nodes[0], final), readObserverReorgInventory(t, nodes[1], final)
	if !reflect.DeepEqual(left, right) {
		t.Fatal("settled node ticket inventories differ")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "final-ledger.json"), map[string]interface{}{"Header": final.Header(), "Tickets": left}))
	var status observe.HistoryStatus
	for _, node := range config.Nodes {
		result := invoke(node.Name+"-settled-backfill", false, "--config", maintenance, "--history", history, "--timeout", "5s", "--backfill-node", node.Name, "--backfill-blocks", "128")
		coverage := requireMiningCoverage(t, result.raw, node.Name, "complete_at_observation")
		if coverage.StoredThrough.Hash != final.Hash() {
			t.Fatal("settled backfill differs from executed head")
		}
		requireNoError(t, json.Unmarshal(result.raw, &status))
	}
	settledExport := invoke("settled-export", false, "--history", history, "--history-export").raw
	if !bytes.HasPrefix(settledExport, initialExport) {
		t.Fatal("mixed workload rewrote the pre-production evidence")
	}
	for _, mode := range []string{"snapshot", "backfill"} {
		rejected := false
		for attempt := 1; attempt <= 64; attempt++ {
			args := []string{"--config", maintenance, "--history", history, "--timeout", "5s"}
			if mode == "backfill" {
				args = append(args, "--backfill-node", config.Nodes[0].Name, "--backfill-blocks", "128")
			}
			result := invoke(fmt.Sprintf("fill-%s-%02d", mode, attempt), true, args...)
			if result.ExitCode == 1 {
				rejected = true
				break
			}
			if mode == "snapshot" {
				var saved struct{ History observe.HistoryStatus }
				requireNoError(t, json.Unmarshal(result.raw, &saved))
				status = saved.History
			} else {
				requireNoError(t, json.Unmarshal(result.raw, &status))
			}
		}
		if !rejected {
			t.Fatal("bounded fill did not reach the explicit history budget")
		}
		var after observe.HistoryStatus
		requireNoError(t, json.Unmarshal(invoke(mode+"-rejected-status", false, "--history", history, "--history-status").raw, &after))
		if !reflect.DeepEqual(after, status) {
			t.Fatal("rejected append changed persisted history status")
		}
	}
	beforeRetry := invoke("before-retry-export", false, "--history", history, "--history-export").raw
	for _, mode := range []string{"snapshot", "backfill"} {
		args := []string{"--config", maintenance, "--history", history, "--timeout", "5s"}
		if mode == "backfill" {
			args = append(args, "--backfill-node", config.Nodes[0].Name, "--backfill-blocks", "128")
		}
		if invoke("retry-"+mode, true, args...).ExitCode != 1 {
			t.Fatal("exhausted write unexpectedly succeeded on retry")
		}
	}
	for _, node := range nodes {
		node.stop(t, false)
	}
	nodes = [2]*rehearsalNode{}
	var reopened observe.HistoryStatus
	requireNoError(t, json.Unmarshal(invoke("offline-status", false, "--history", history, "--history-status").raw, &reopened))
	if !reflect.DeepEqual(reopened, status) {
		t.Fatal("offline reopening changed full-history status")
	}
	for _, node := range config.Nodes {
		var timeline observe.TicketTimeline
		requireNoError(t, json.Unmarshal(invoke(node.Name+"-offline-timeline", false, "--history", history, "--ticket-timeline", node.Name, "--ticket-blocks", "128").raw, &timeline))
		expected := make(map[common.Hash]common.TicketDisplay)
		for id, ticket := range left {
			if ticket.Owner == node.Wallet {
				expected[id] = ticket
			}
		}
		if timeline.Status != "complete_for_retained_prefix" || timeline.Through == nil || timeline.Through.Hash != final.Hash() || !reflect.DeepEqual(timeline.Inventory, expected) {
			t.Fatal("full-history offline timeline differs from settled executed state")
		}
	}
	finalExport := invoke("offline-export", false, "--history", history, "--history-export").raw
	if !bytes.Equal(finalExport, beforeRetry) || !bytes.HasPrefix(finalExport, settledExport) {
		t.Fatal("budget rejection, retries or offline queries rewrote evidence")
	}
	var fileBytes int64
	requireNoError(t, filepath.Walk(history, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.Mode().IsRegular() {
			fileBytes += info.Size()
		}
		return nil
	}))
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "commands.json"), commands))
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "result.json"), map[string]interface{}{"Passed": true, "Producer": config.Nodes[producer].Name, "Anchor": anchor.Header(), "Final": final.Header(), "Rounds": 6, "LogicalBytes": status.LogicalBytes, "BudgetBytes": status.MaxBytes, "ClosedFileBytes": fileBytes, "OrdinaryMining": true, "RuntimeChanges": false, "LargeBackupRead": false, "PublicTestKeys": []int{1, 2}}))
	t.Logf("mixed IPC/HTTP workload passed: final=%d budget=%d retained=%d; rejected writes preserved status, exports and both offline inventories", final.NumberU64(), status.MaxBytes, status.LogicalBytes)
}
