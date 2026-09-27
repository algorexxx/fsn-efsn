package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func TestObserverOrdinaryMining(t *testing.T) {
	output, binary := os.Getenv("FUSION_RESTART_OBSERVER_MINING_RESULTS"), os.Getenv("FUSION_RESTART_OBSERVER_BIN")
	if output == "" || binary == "" {
		t.Skip("requires an explicitly built observer and isolated mining evidence directory")
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
	owners := []common.Address{pair.miners[0].owner, pair.miners[1].owner}
	config := observe.Config{ChainID: pair.genesis.Config.ChainID.String(), NetworkID: "99032659", Genesis: pair.miners[0].chain.Genesis().Hash(), AnchorNumber: anchor.NumberU64(), AnchorHash: anchor.Hash()}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "genesis.json"), pair.genesis))
	closeDenseMinerPair(t, pair)
	for i, path := range pair.paths {
		var lab nodeRehearsalConfig
		readHandoverJSON(t, filepath.Join(path, "lab.json"), &lab)
		lab.HTTP = true
		requireNoError(t, os.WriteFile(filepath.Join(path, "lab.json"), mustObserverJSON(t, lab), 0600))
		role := "verifier"
		if i == producer {
			role = "producer"
		}
		config.Nodes = append(config.Nodes, observe.NodeConfig{Name: fmt.Sprintf("node-%d", i+1), Endpoint: filepath.Join(path, "lab.ipc"), Wallet: owners[i], Role: role})
	}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, pair.paths[0], 8*time.Minute), startRehearsalNodeWithTimeout(t, pair.paths[1], 8*time.Minute)}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	ipcConfig := filepath.Join(output, "ipc-config.json")
	requireNoError(t, writeStateExportJSON(ipcConfig, config))
	maintenance := config
	maintenance.Nodes = append([]observe.NodeConfig(nil), config.Nodes...)
	for i := range maintenance.Nodes {
		maintenance.Nodes[i].Role = "maintenance"
	}
	maintenancePath := filepath.Join(output, "maintenance-config.json")
	requireNoError(t, writeStateExportJSON(maintenancePath, maintenance))
	httpConfig := config
	httpConfig.Nodes = append([]observe.NodeConfig(nil), config.Nodes...)
	for i, node := range nodes {
		var endpoint []byte
		awaitRehearsal(t, time.Second, func() bool {
			var err error
			endpoint, err = os.ReadFile(filepath.Join(node.path, "http.endpoint"))
			return err == nil
		})
		httpConfig.Nodes[i].Endpoint = string(endpoint)
	}
	history := filepath.Join(t.TempDir(), "observer-history")
	invoke := func(name string, mining bool, args ...string) []byte {
		return runMiningObserver(t, binary, output, name, nodes, producer, mining, args...)
	}
	invoke("init", false, "--config", maintenancePath, "--history", history, "--init-history", "--history-budget", "16777216")
	initial := invoke("anchor-snapshot", false, "--config", maintenancePath, "--history", history, "--timeout", "5s")
	startCompetingMiner(t, nodes[producer])
	awaitRehearsal(t, 120*time.Second, func() bool {
		return nodes[0].status(t).Number >= 27 && nodes[1].status(t).Number >= 27 && readPeerPurchase(t, nodes[producer]).Nonce >= 26
	})
	partial := invoke("ipc-partial", true, "--config", ipcConfig, "--history", history, "--timeout", "5s", "--backfill-node", config.Nodes[producer].Name, "--backfill-blocks", "1")
	partialState := requireMiningCoverage(t, partial, config.Nodes[producer].Name, "batch_limit")
	if partialState.StoredThrough.Number != 25 {
		t.Fatal("bounded live backlog skipped a block")
	}
	for _, mode := range []string{"snapshot", "backfill"} {
		method := "eth_getTransactionCount"
		if mode == "backfill" {
			method = "eth_getBlockByNumber"
		}
		proxy := newObserverMiningProxy(t, nodes[producer], httpConfig.Nodes[producer].Endpoint, method)
		proxyConfig := httpConfig
		proxyConfig.Nodes = append([]observe.NodeConfig(nil), httpConfig.Nodes...)
		proxyConfig.Nodes[producer].Endpoint = proxy.server.URL
		path := filepath.Join(output, "moving-"+mode+"-config.json")
		requireNoError(t, writeStateExportJSON(path, proxyConfig))
		args := []string{"--config", path, "--history", history, "--timeout", "75s"}
		if mode == "backfill" {
			args = append(args, "--backfill-node", config.Nodes[producer].Name, "--backfill-blocks", "2")
		}
		raw := invoke("moving-"+mode, true, args...)
		window := proxy.result()
		requireNoError(t, writeStateExportJSON(filepath.Join(output, "moving-"+mode+"-window.json"), window))
		if window.Error != "" || !window.Completed || window.AdvancedHeight <= window.PinnedHeight {
			t.Fatalf("read did not overlap natural mining: %+v", window)
		}
		if mode == "snapshot" {
			var report observe.Report
			requireNoError(t, json.Unmarshal(raw, &report))
			observed := report.Nodes[producer]
			if observed.Head.Header.Number.Uint64() != window.PinnedHeight || observed.Consistency != "stable" || observed.Identity != "matches" || !observed.TicketsKnown || len(observed.Issues) != 0 {
				t.Fatal("head advancement invalidated the unchanged historical snapshot", observed.Issues)
			}
		} else {
			coverage := requireMiningCoverage(t, raw, config.Nodes[producer].Name, "batch_limit")
			if coverage.ObservedHead.Number != window.PinnedHeight || coverage.StoredThrough.Number != 27 {
				t.Fatal("moving backfill changed its target or skipped the batch bound")
			}
		}
		proxy.server.Close()
	}
	httpPath := filepath.Join(output, "http-config.json")
	requireNoError(t, writeStateExportJSON(httpPath, httpConfig))
	for i, path := range []string{ipcConfig, httpPath} {
		raw := invoke(fmt.Sprintf("live-catchup-%d", i+1), true, "--config", path, "--history", history, "--timeout", "10s", "--backfill-node", config.Nodes[i].Name, "--backfill-blocks", "128")
		requireMiningCoverage(t, raw, config.Nodes[i].Name, "complete_at_observation")
	}
	stopPeerAutoMiner(t, nodes[producer])
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	if final.NumberU64() < 29 {
		t.Fatal("expected multiple ordinary blocks spanning both delayed reads")
	}
	for i := range nodes {
		raw := invoke(fmt.Sprintf("final-catchup-%d", i+1), false, "--config", ipcConfig, "--history", history, "--timeout", "10s", "--backfill-node", config.Nodes[i].Name, "--backfill-blocks", "128")
		coverage := requireMiningCoverage(t, raw, config.Nodes[i].Name, "complete_at_observation")
		if coverage.StoredThrough.Hash != final.Hash() {
			t.Fatal("final coverage is not the settled common head")
		}
	}
	exported := invoke("history-export", false, "--history", history, "--history-export")
	counts := auditObserverMiningHistory(t, output, initial, exported, config, nodes, producer, final)
	auditPartitionFunds(t, nodes[0], owners, anchor.NumberU64(), final.NumberU64(), "observer-ordinary-mining")
	for i, node := range nodes {
		node.stop(t, false)
		nodes[i] = startRehearsalNode(t, node.path)
		requireRehearsalHead(t, nodes[i].status(t), final)
	}
	for i := range nodes {
		raw := invoke(fmt.Sprintf("cold-recheck-%d", i+1), false, "--config", ipcConfig, "--history", history, "--timeout", "10s", "--backfill-node", config.Nodes[i].Name, "--backfill-blocks", "128")
		coverage := requireMiningCoverage(t, raw, config.Nodes[i].Name, "complete_at_observation")
		if coverage.StoredThrough.Hash != final.Hash() {
			t.Fatal("cold node or reopened observer changed coverage")
		}
	}
	invoke("cold-history-export", false, "--history", history, "--history-export")
	for _, node := range nodes {
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "result.json"), map[string]interface{}{"Passed": true, "Producer": config.Nodes[producer].Name, "Anchor": anchor.Header(), "Final": final.Header(), "Counts": counts, "PublicTestKeys": []int{1, 2}, "OrdinaryMining": true, "HeldSigner": false, "ControlledDownloader": false, "LargeBackupRead": false, "NodeRuntimeChanges": false}))
	t.Logf("ordinary mining observer passed: producer=%s range=%d..%d final=%s counts=%v; moving IPC/HTTP collection, bounded catch-up, both cold nodes and retained evidence agree", config.Nodes[producer].Name, anchor.NumberU64()+1, final.NumberU64(), final.Hash().Hex(), counts)
}

func runMiningObserver(t *testing.T, binary, output, name string, nodes [2]*rehearsalNode, producer int, mining bool, args ...string) []byte {
	t.Helper()
	before := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, binary, args...)
	var stdout, stderr bytes.Buffer
	command.Stdout, command.Stderr = &stdout, &stderr
	started := time.Now().UTC()
	err := command.Run()
	suffix := ".json"
	if name == "history-export" || name == "cold-history-export" {
		suffix = ".jsonl"
	}
	requireNoError(t, os.WriteFile(filepath.Join(output, name+suffix), stdout.Bytes(), 0600))
	requireNoError(t, os.WriteFile(filepath.Join(output, name+"-stderr.txt"), stderr.Bytes(), 0600))
	if err != nil || stderr.Len() != 0 {
		t.Fatalf("observer exit=%v stderr=%s", err, stderr.Bytes())
	}
	after := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	for i := range nodes {
		expected := mining && i == producer
		if before[i].Mining != expected || before[i].AutoBuy != expected || after[i].Mining != expected || after[i].AutoBuy != expected || after[i].Number < before[i].Number || after[i].Signatures < before[i].Signatures || i != producer && after[i].Signatures != 0 {
			t.Fatal("observer control boundary or one-producer progression differs")
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, name+"-command.json"), map[string]interface{}{"StartedUTC": started, "FinishedUTC": time.Now().UTC(), "Before": before, "After": after, "MiningExpected": mining, "ProducerIndex": producer}))
	return stdout.Bytes()
}

func requireMiningCoverage(t *testing.T, raw []byte, node, expected string) observe.BlockCoverage {
	t.Helper()
	var status observe.HistoryStatus
	requireNoError(t, json.Unmarshal(raw, &status))
	for _, coverage := range status.Blocks {
		if coverage.Node == node {
			if coverage.Status != expected {
				t.Fatalf("unexpected mining coverage: %+v", coverage)
			}
			return coverage
		}
	}
	t.Fatal("missing node coverage")
	return observe.BlockCoverage{}
}
