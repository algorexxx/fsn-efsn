package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

type observerReorgCase struct {
	mode    string
	output  string
	history string
	before  []byte
	proxy   *observerMiningProxy
	ready   chan observerMiningWindow
	release chan uint64
	pinned  observerMiningWindow
	command *observerReorgCommand
}

func TestObserverCompetingReorganization(t *testing.T) {
	output, binary := os.Getenv("FUSION_RESTART_OBSERVER_REORG_RESULTS"), os.Getenv("FUSION_RESTART_OBSERVER_BIN")
	if output == "" || binary == "" {
		t.Skip("requires a built observer and isolated competing-miner evidence directory")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(output) || !filepath.IsAbs(binary) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute observer/evidence paths, isolated rehearsal and no backup input required")
	}
	requireNoError(t, os.Mkdir(output, 0700))
	pair := seedDenseMinerPair(t)
	anchor := pair.miners[0].chain.CurrentBlock()
	owners := []common.Address{pair.miners[0].owner, pair.miners[1].owner}
	config := observe.Config{ChainID: pair.genesis.Config.ChainID.String(), NetworkID: "99032659", Genesis: pair.miners[0].chain.Genesis().Hash(), AnchorNumber: anchor.NumberU64(), AnchorHash: anchor.Hash()}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "genesis.json"), pair.genesis))
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "anchor-truth.json"), []observerServiceTruth{captureObserverTruth(t, pair.miners[0], owners[0]), captureObserverTruth(t, pair.miners[1], owners[1])}))
	closeDenseMinerPair(t, pair)
	for i, path := range pair.paths {
		var lab nodeRehearsalConfig
		readHandoverJSON(t, filepath.Join(path, "lab.json"), &lab)
		lab.HTTP = true
		requireNoError(t, os.WriteFile(filepath.Join(path, "lab.json"), mustObserverJSON(t, lab), 0600))
		config.Nodes = append(config.Nodes, observe.NodeConfig{Name: fmt.Sprintf("node-%d", i+1), Endpoint: filepath.Join(path, "lab.ipc"), Wallet: owners[i], Role: "maintenance"})
	}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, pair.paths[0], 8*time.Minute), startRehearsalNodeWithTimeout(t, pair.paths[1], 8*time.Minute)}
	ipcPath := filepath.Join(output, "ipc-config.json")
	requireNoError(t, writeStateExportJSON(ipcPath, config))
	cases := []*observerReorgCase{}
	for _, mode := range []string{"snapshot", "backfill"} {
		probe := &observerReorgCase{mode: mode, output: filepath.Join(output, mode), history: filepath.Join(t.TempDir(), "history"), ready: make(chan observerMiningWindow, 1), release: make(chan uint64, 1)}
		requireNoError(t, os.Mkdir(probe.output, 0700))
		runServiceHistory(t, binary, probe.output, "init", nodes, "--config", ipcPath, "--history", probe.history, "--init-history", "--history-budget", "16777216")
		for _, node := range config.Nodes {
			var inventory observe.AnchorInventory
			raw := runServiceHistory(t, binary, probe.output, node.Name+"-anchor", nodes, "--config", ipcPath, "--history", probe.history, "--timeout", "5s", "--anchor-inventory", node.Name)
			requireNoError(t, json.Unmarshal(raw, &inventory))
			if inventory.Status != "ready" || inventory.Anchor.Hash != anchor.Hash() {
				t.Fatal("pre-production baseline unavailable")
			}
		}
		cases = append(cases, probe)
	}
	startCompetingMiner(t, nodes[0])
	awaitRehearsal(t, 90*time.Second, func() bool { return nodes[0].status(t).Number >= anchor.NumberU64()+3 })
	startCompetingMiner(t, nodes[1])
	awaitRehearsal(t, 90*time.Second, func() bool { return nodes[1].status(t).Number >= anchor.NumberU64()+2 })
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 0, time.Second)
	var isolated []*types.Header
	for i, node := range nodes {
		block := readRecoveryNodeBlock(t, node, anchor.NumberU64()+1)
		if block.ParentHash() != anchor.Hash() || block.Coinbase() != owners[i] {
			t.Fatal("isolated ordinary miner did not produce its own descendant")
		}
		isolated = append(isolated, block.Header())
	}
	if isolated[0].Hash() == isolated[1].Hash() {
		t.Fatal("isolated miners did not produce different branches")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "isolated-first-blocks.json"), isolated))
	winner, loser := orderPeerDifficulty(t, nodes[0], nodes[1])
	loserIndex := 0
	if loser == nodes[1] {
		loserIndex = 1
	}
	if winner.status(t).Number <= loser.status(t).Number || (*big.Int)(winner.status(t).TD).Cmp((*big.Int)(loser.status(t).TD)) <= 0 {
		t.Fatal("staggered ordinary miners did not produce a taller heavier branch")
	}
	loserName := config.Nodes[loserIndex].Name
	for i := range config.Nodes {
		config.Nodes[i].Role = "producer"
	}
	for height := anchor.NumberU64() + 1; height <= loser.status(t).Number && len(config.Tracked) == 0; height++ {
		for _, tx := range readRecoveryNodeBlock(t, loser, height).Transactions() {
			if tx.IsBuyTicketTx() {
				raw, err := tx.MarshalBinary()
				requireNoError(t, err)
				config.Tracked = append(config.Tracked, raw)
				break
			}
		}
	}
	if len(config.Tracked) != 1 {
		t.Fatal("isolated loser did not produce a purchase to track")
	}
	activePath := filepath.Join(output, "active-config.json")
	requireNoError(t, writeStateExportJSON(activePath, config))
	endpoint, err := os.ReadFile(filepath.Join(loser.path, "http.endpoint"))
	requireNoError(t, err)
	for _, probe := range cases {
		probe := probe
		for _, node := range config.Nodes {
			command := startObserverReorgCommand(t, binary, nodes, "--config", activePath, "--history", probe.history, "--timeout", "5s", "--backfill-node", node.Name, "--backfill-blocks", "128")
			raw := finishObserverReorgCommand(t, command, probe.output, node.Name+"-isolated", nodes)
			requireMiningCoverage(t, raw, node.Name, "complete_at_observation")
		}
		command := startObserverReorgCommand(t, binary, nodes, "--history", probe.history, "--history-export")
		probe.before = finishObserverReorgCommand(t, command, probe.output, "before-export", nodes)
		method := "eth_getTransactionCount"
		if probe.mode == "backfill" {
			method = "eth_getBlockByNumber"
		}
		probe.proxy = newObserverMiningProxy(t, loser, string(endpoint), method)
		probe.proxy.mu.Lock()
		probe.proxy.gate = func(ctx context.Context, window observerMiningWindow) (uint64, error) {
			probe.ready <- window
			select {
			case height := <-probe.release:
				return height, nil
			case <-ctx.Done():
				return 0, ctx.Err()
			}
		}
		probe.proxy.mu.Unlock()
		moving := config
		moving.Nodes = append([]observe.NodeConfig(nil), config.Nodes...)
		moving.Nodes[loserIndex].Endpoint = probe.proxy.server.URL
		path := filepath.Join(probe.output, "moving-config.json")
		requireNoError(t, writeStateExportJSON(path, moving))
		args := []string{"--config", path, "--history", probe.history, "--timeout", "90s"}
		if probe.mode == "backfill" {
			args = append(args, "--backfill-node", loserName, "--backfill-blocks", "128")
		}
		probe.command = startObserverReorgCommand(t, binary, nodes, args...)
		select {
		case probe.pinned = <-probe.ready:
		case <-time.After(10 * time.Second):
			t.Fatal("observer did not reach the branch-change gate")
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "before-connect.json"), []nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}))
	connectRehearsalPeer(t, loser, winner)
	awaitRehearsal(t, 90*time.Second, func() bool {
		for _, probe := range cases {
			if loser.status(t).Number < probe.pinned.PinnedHeight || winner.status(t).Number < probe.pinned.PinnedHeight {
				return false
			}
			left := readRecoveryNodeBlock(t, loser, probe.pinned.PinnedHeight)
			right := readRecoveryNodeBlock(t, winner, probe.pinned.PinnedHeight)
			if left.Hash() == probe.pinned.PinnedHash || left.Hash() != right.Hash() {
				return false
			}
		}
		return true
	})
	for _, probe := range cases {
		replacement := readRecoveryNodeBlock(t, loser, probe.pinned.PinnedHeight)
		requireNoError(t, writeStateExportJSON(filepath.Join(probe.output, "replacement-at-pinned-height.json"), replacement.Header()))
		probe.release <- loser.status(t).Number
		raw := finishObserverReorgCommand(t, probe.command, probe.output, "during-reorg", nodes)
		requireNoError(t, writeStateExportJSON(filepath.Join(probe.output, "window.json"), probe.proxy.result()))
		if probe.mode == "snapshot" {
			var report observe.Report
			requireNoError(t, json.Unmarshal(raw, &report))
			observed := report.Nodes[loserIndex]
			if observed.Consistency != "changed_or_unavailable" || observed.Head.Hash != probe.pinned.PinnedHash || len(observed.Tracked) != 1 || observed.Tracked[0].Inclusion != "unknown" || observed.Tracked[0].Funding != "unknown" {
				t.Fatal("snapshot crossing a live branch change retained authoritative classification")
			}
		} else {
			requireMiningCoverage(t, raw, loserName, "unstable")
		}
		probe.proxy.server.Close()
	}
	awaitRehearsal(t, 20*time.Second, func() bool { return nodes[0].status(t).Mining && nodes[1].status(t).Mining })
	stopPeerAutoMiner(t, nodes[0])
	stopPeerAutoMiner(t, nodes[1])
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	left := readPartitionFunds(t, nodes[0], owners, final.NumberU64())
	right := readPartitionFunds(t, nodes[1], owners, final.NumberU64())
	if !bytes.Equal(mustObserverJSON(t, left.Tickets), mustObserverJSON(t, right.Tickets)) {
		t.Fatal("settled node inventories differ")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "final-ledger.json"), map[string]interface{}{"Header": final.Header(), "Tickets": left.Tickets, "Accounts": left.Accounts}))
	for _, probe := range cases {
		finishObserverReorgHistory(t, binary, probe, nodes, config, ipcPath, loserName, final, left.Tickets)
	}
	for i, node := range nodes {
		node.stop(t, false)
		nodes[i] = startRehearsalNode(t, node.path)
		requireRehearsalHead(t, nodes[i].status(t), final)
	}
	for _, probe := range cases {
		for i, node := range config.Nodes {
			expected := observerServiceTruth{Header: final.Header(), Tickets: make(map[common.Hash]common.TicketDisplay)}
			for id, ticket := range left.Tickets {
				if ticket.Owner == owners[i] {
					expected.Tickets[id] = ticket
				}
			}
			requireServiceTicketTimeline(t, binary, probe.output, node.Name+"-cold-timeline", probe.history, nodes, node.Name, expected)
		}
	}
	for _, node := range nodes {
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "result.json"), map[string]interface{}{"Passed": true, "Loser": loserName, "Anchor": anchor.Header(), "Final": final.Header(), "PublicTestKeys": []int{1, 2}, "OrdinaryMining": true, "HeldSigner": false, "ControlledDownloader": false, "LargeBackupRead": false, "RuntimeChanges": false}))
	t.Logf("live reorganization observer passed: displaced=%s anchor=%d final=%d; snapshot invalidated, backfill unstable, original evidence retained, both inventories and cold heads agree", loserName, anchor.NumberU64(), final.NumberU64())
}

func finishObserverReorgHistory(t *testing.T, binary string, probe *observerReorgCase, nodes [2]*rehearsalNode, config observe.Config, path, loserName string, final *types.Block, tickets map[common.Hash]common.TicketDisplay) {
	t.Helper()
	during := runServiceHistory(t, binary, probe.output, "during-export", nodes, "--history", probe.history, "--history-export")
	if !bytes.HasPrefix(during, probe.before) {
		t.Fatal("collection crossing a reorganization rewrote original history")
	}
	if probe.mode == "backfill" {
		lines := bytes.Split(bytes.TrimSpace(during), []byte{'\n'})
		var event struct{ Backfill *observe.BackfillReport }
		requireNoError(t, json.Unmarshal(lines[len(lines)-1], &event))
		if event.Backfill == nil || event.Backfill.Status != "unstable" || event.Backfill.Base != nil || len(event.Backfill.Blocks) != 0 {
			t.Fatal("unstable backfill retained a potentially mixed branch")
		}
	}
	var last []byte
	for _, node := range config.Nodes {
		raw := runServiceHistory(t, binary, probe.output, node.Name+"-final-backfill", nodes, "--config", path, "--history", probe.history, "--timeout", "10s", "--backfill-node", node.Name, "--backfill-blocks", "128")
		coverage := requireMiningCoverage(t, raw, node.Name, "complete_at_observation")
		if coverage.StoredThrough.Hash != final.Hash() {
			t.Fatal("retry did not reach settled canonical head")
		}
		expected := observerServiceTruth{Header: final.Header(), Tickets: make(map[common.Hash]common.TicketDisplay)}
		for id, ticket := range tickets {
			if ticket.Owner == node.Wallet {
				expected.Tickets[id] = ticket
			}
		}
		requireServiceTicketTimeline(t, binary, probe.output, node.Name+"-final-timeline", probe.history, nodes, node.Name, expected)
		last = raw
	}
	var status observe.HistoryStatus
	requireNoError(t, json.Unmarshal(last, &status))
	changed := false
	for _, incident := range status.Incidents {
		if incident.Kind == "canonical_history_change" && incident.Node == loserName && incident.Status == "open" {
			changed = true
		}
	}
	if !changed {
		t.Fatal("canonical branch replacement was not retained as an open incident")
	}
	finalExport := runServiceHistory(t, binary, probe.output, "final-export", nodes, "--history", probe.history, "--history-export")
	if !bytes.HasPrefix(finalExport, during) {
		t.Fatal("canonical catch-up discarded displaced evidence")
	}
}
