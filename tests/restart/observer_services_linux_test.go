package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type observerServiceTruth struct {
	Header    *types.Header
	TD        *big.Int
	Nonce     uint64
	LiquidWei string
	TimeLocks *common.TimeLock
	Tickets   map[common.Hash]common.TicketDisplay
}

func TestObserverNodeServices(t *testing.T) {
	output := os.Getenv("FUSION_RESTART_OBSERVER_RESULTS")
	binary := os.Getenv("FUSION_RESTART_OBSERVER_BIN")
	if output == "" || binary == "" {
		t.Skip("requires an explicitly built observer and isolated service evidence directory")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(output) || !filepath.IsAbs(binary) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute observer/evidence paths, isolated rehearsal and no backup input required")
	}
	requireNoError(t, os.Mkdir(output, 0700))
	pair := seedDenseMinerPair(t)
	first, second := pair.miners[0], pair.miners[1]
	anchor := first.chain.CurrentBlock()
	var prior *types.Transaction
	for _, tx := range anchor.Transactions() {
		owner, err := types.Sender(types.LatestSigner(first.chain.Config()), tx)
		requireNoError(t, err)
		if owner == first.owner {
			prior = tx
		}
	}
	if prior == nil || prior.Nonce() != 23 {
		t.Fatal("expected the independently executed owner-one purchase at block 24")
	}
	purchase := first.signPurchase(t, anchor.Time(), common.TimeLockForever)
	cancel, err := types.SignTx(types.NewTransaction(24, first.owner, new(big.Int), 21000, purchase.GasPrice(), nil), types.LatestSigner(first.chain.Config()), first.key)
	requireNoError(t, err)
	future, err := types.SignTx(types.NewTransaction(26, *purchase.To(), purchase.Value(), purchase.Gas(), purchase.GasPrice(), purchase.Data()), types.LatestSigner(first.chain.Config()), first.key)
	requireNoError(t, err)
	local := first.buildBlockWithTransactions(t, anchor.Time()+120, []*types.Transaction{purchase})
	first.importBlock(t, local)
	remote := second.buildBlockWithTransactions(t, anchor.Time()+121, []*types.Transaction{cancel})
	second.importBlock(t, remote)
	final := second.buildBlock(t, remote.Time()+120, false)
	second.importBlock(t, final)
	truth := [2]observerServiceTruth{captureObserverTruth(t, first, first.owner), captureObserverTruth(t, second, first.owner)}
	if truth[1].TD.Cmp(truth[0].TD) <= 0 || purchase.Nonce() != 24 {
		t.Fatal("expected a heavier alternate branch and original purchase nonce 24")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "prepared-truth.json"), truth))
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "genesis.json"), pair.genesis))
	for name, block := range map[string]*types.Block{"anchor": anchor, "local-25": local, "remote-25": remote, "remote-26": final} {
		raw, err := rlp.EncodeToBytes(block)
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(output, name+".rlp"), raw, 0600))
	}
	config := observe.Config{ChainID: first.chain.Config().ChainID.String(), NetworkID: "99032659", Genesis: first.chain.Genesis().Hash(), AnchorNumber: anchor.NumberU64(), AnchorHash: anchor.Hash()}
	for _, tx := range []*types.Transaction{prior, purchase, cancel, future} {
		raw, err := tx.MarshalBinary()
		requireNoError(t, err)
		config.Tracked = append(config.Tracked, raw)
	}
	for i, f := range pair.miners {
		closeTwoMinerSeed(t, pair.paths[i], f, anchor, byte(i+1))
		var lab nodeRehearsalConfig
		path := filepath.Join(pair.paths[i], "lab.json")
		readHandoverJSON(t, path, &lab)
		lab.DenseGenesis, lab.HTTP = pair.genesis, true
		requireNoError(t, os.WriteFile(path, mustObserverJSON(t, lab), 0600))
		config.Nodes = append(config.Nodes, observe.NodeConfig{Name: fmt.Sprintf("node-%d", i+1), Endpoint: filepath.Join(pair.paths[i], "lab.ipc"), Role: "maintenance", Wallet: first.owner})
	}
	nodes := [2]*rehearsalNode{startRehearsalNode(t, pair.paths[0]), startRehearsalNode(t, pair.paths[1])}
	initial := runServiceObserver(t, binary, output, "ipc-divergence", config, nodes)
	historyPath := ""
	if os.Getenv("FUSION_RESTART_OBSERVER_BACKFILL") == "1" {
		historyPath = filepath.Join(t.TempDir(), "observer-history")
		runServiceHistory(t, binary, output, "history-init", nodes, "--config", filepath.Join(output, "ipc-divergence-config.json"), "--history", historyPath, "--init-history", "--history-budget", "16777216")
		runServiceHistory(t, binary, output, "history-initial-snapshot", nodes, "--config", filepath.Join(output, "ipc-divergence-config.json"), "--history", historyPath, "--timeout", "5s")
		requireServiceBackfill(t, binary, output, "backfill-local", "ipc-divergence", historyPath, nodes, "node-1", local, "complete_at_observation")
	}
	requireObserverTruth(t, initial, truth)
	if initial.Comparison.Status != "divergent_at_common_height" || initial.Comparison.Height != 25 {
		t.Fatal("real fork not detected", initial.Comparison)
	}
	for i, node := range initial.Nodes {
		want := [2][4]string{{"canonical_native_success", "canonical_native_success", "absent", "absent"}, {"canonical_native_success", "absent", "canonical_ordinary_success", "absent"}}
		for j, tracked := range node.Tracked {
			if tracked.Inclusion != want[i][j] {
				t.Fatalf("node %d transaction %d: inclusion=%s, expected %s; issues=%v", i, j, tracked.Inclusion, want[i][j], node.Issues)
			}
		}
		if node.Tracked[3].NonceRelation != "ahead" || node.Tracked[3].Funding != "available_estimate" || node.Peers == nil || *node.Peers != 0 {
			t.Fatal("real nonce gap/funding or zero-peer observation differs")
		}
	}
	httpConfig := config
	httpConfig.Nodes = append([]observe.NodeConfig(nil), config.Nodes...)
	for i, node := range nodes {
		var endpoint []byte
		awaitRehearsal(t, time.Second, func() bool {
			endpoint, err = os.ReadFile(filepath.Join(node.path, "http.endpoint"))
			return err == nil
		})
		httpConfig.Nodes[i].Endpoint = string(endpoint)
	}
	httpReport := runServiceObserver(t, binary, output, "http-divergence", httpConfig, nodes)
	requireObserverTruth(t, httpReport, truth)
	if httpReport.Comparison.Status != initial.Comparison.Status {
		t.Fatal("HTTP and IPC disagree on the fork")
	}
	for i := range initial.Nodes {
		a, _ := json.Marshal(initial.Nodes[i].Tracked)
		b, _ := json.Marshal(httpReport.Nodes[i].Tracked)
		if !bytes.Equal(a, b) {
			t.Fatal("HTTP and IPC disagree on transaction observations")
		}
	}
	if historyPath != "" {
		requireServiceBackfill(t, binary, output, "backfill-http-partial", "http-divergence", historyPath, nodes, "node-2", remote, "batch_limit")
		requireServiceBackfill(t, binary, output, "backfill-http-complete", "http-divergence", historyPath, nodes, "node-2", final, "complete_at_observation")
	}
	syncRecoveryNode(t, nodes[0], nodes[1], final)
	truth[0] = truth[1]
	converged := runServiceObserver(t, binary, output, "ipc-converged", config, nodes)
	requireObserverTruth(t, converged, truth)
	if converged.Comparison.Status != "same_at_common_height" || converged.Nodes[0].Tracked[1].Inclusion != "absent" || converged.Nodes[0].Tracked[2].Inclusion != "canonical_ordinary_success" {
		t.Fatal("observer failed to invalidate the displaced purchase after synchronization")
	}
	if historyPath != "" {
		runServiceHistory(t, binary, output, "history-converged-snapshot", nodes, "--config", filepath.Join(output, "ipc-converged-config.json"), "--history", historyPath, "--timeout", "5s")
		requireServiceBackfill(t, binary, output, "backfill-reorg-partial", "ipc-converged", historyPath, nodes, "node-1", remote, "batch_limit")
		requireServiceBackfill(t, binary, output, "backfill-reorg-complete", "ipc-converged", historyPath, nodes, "node-1", final, "complete_at_observation")
		raw := runServiceHistory(t, binary, output, "history-export", nodes, "--history", historyPath, "--history-export")
		for _, block := range []*types.Block{local, remote, final} {
			encoded, err := rlp.EncodeToBytes(block)
			requireNoError(t, err)
			if !bytes.Contains(raw, []byte(fmt.Sprintf("0x%x", encoded))) {
				t.Fatal("service backfill lost original or replacement block bytes")
			}
		}
	}
	var submitted common.Hash
	requireNoError(t, nodes[0].call(t, &submitted, "eth_sendRawTransaction", config.Tracked[3]))
	if submitted != future.Hash() {
		t.Fatal("test submission changed signed bytes")
	}
	awaitRehearsal(t, 3*time.Second, func() bool {
		state := readPeerPurchase(t, nodes[0])
		return len(state.Queued) == 1 && state.Queued[0].Hash() == future.Hash()
	})
	queued := runServiceObserver(t, binary, output, "ipc-queued-gap", config, nodes)
	if queued.Nodes[0].Tracked[3].Pool != "queued" || queued.Nodes[0].Tracked[3].NonceRelation != "ahead" || queued.Nodes[0].Tracked[3].Inclusion != "absent" {
		t.Fatal("actual queued transaction not classified as an unmined nonce gap")
	}
	config.Nodes[0].Role = "producer"
	disabled := runServiceObserver(t, binary, output, "ipc-disabled-producer", config, nodes)
	if !bytes.Contains(mustObserverJSON(t, disabled.Nodes[0].Issues), []byte("disabled_observed")) {
		t.Fatal("disabled producer flags were hidden")
	}
	config.Nodes[0].Role = "maintenance"
	config.NetworkID = "1"
	mismatch := runServiceObserver(t, binary, output, "ipc-wrong-identity", config, nodes)
	if mismatch.Comparison.Status != "unavailable" || mismatch.Nodes[0].Identity != "mismatch" || mismatch.Nodes[0].Tracked[0].Inclusion != "unknown" {
		t.Fatal("identity mismatch retained authoritative classification")
	}
	config.NetworkID = "99032659"
	nodes[1].stop(t, false)
	if historyPath != "" {
		requireServiceBackfill(t, binary, output, "backfill-endpoint-lost", "ipc-converged", historyPath, nodes, "node-2", final, "unavailable")
	}
	lost := runServiceObserver(t, binary, output, "ipc-endpoint-lost", config, nodes)
	if lost.Comparison.Status != "unavailable" || lost.Nodes[1].Head != nil || len(lost.Nodes[1].Issues) == 0 {
		t.Fatal("lost service treated as agreement or zero state")
	}
	config.Nodes[1].Role = "retired"
	retired := runServiceObserver(t, binary, output, "ipc-retired", config, nodes)
	if retired.Nodes[1].Consistency != "not_applicable" || len(retired.Nodes[1].Issues) != 0 || retired.Comparison.Status != "unavailable" {
		t.Fatal("retired endpoint incorrectly faulted or counted as agreement")
	}
	nodes[0].stop(t, false)
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "result.json"), map[string]interface{}{"Passed": true, "Samples": 8, "Anchor": anchor.Hash(), "Final": final.Hash(), "PublicTestKeys": []int{1, 2}, "ObserverMutations": false, "ControlledDownloader": true, "OrdinaryMining": false, "LargeBackupRead": false}))
	t.Log("external observer matched independently executed state over real IPC/HTTP, detected divergence and displaced purchase, classified a real queued nonce gap, disabled producer, wrong identity, lost/retired service; every invocation preserved observed node state")
}

func requireServiceBackfill(t *testing.T, binary, output, name, configName, history string, nodes [2]*rehearsalNode, nodeName string, through *types.Block, status string) {
	t.Helper()
	raw := runServiceHistory(t, binary, output, name, nodes, "--config", filepath.Join(output, configName+"-config.json"), "--history", history, "--timeout", "5s", "--backfill-node", nodeName, "--backfill-blocks", "1")
	var result observe.HistoryStatus
	requireNoError(t, json.Unmarshal(raw, &result))
	for _, coverage := range result.Blocks {
		if coverage.Node == nodeName {
			if coverage.Status != status || coverage.StoredThrough.Number != through.NumberU64() || coverage.StoredThrough.Hash != through.Hash() {
				t.Fatalf("unexpected service block coverage: %+v", coverage)
			}
			return
		}
	}
	t.Fatal("missing service block coverage")
}

func runServiceHistory(t *testing.T, binary, output, name string, nodes [2]*rehearsalNode, args ...string) []byte {
	t.Helper()
	before := captureObserverServices(t, nodes)
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	requireNoError(t, os.WriteFile(filepath.Join(output, name+".json"), stdout.Bytes(), 0600))
	requireNoError(t, os.WriteFile(filepath.Join(output, name+"-stderr.txt"), stderr.Bytes(), 0600))
	if err != nil || stderr.Len() != 0 {
		t.Fatalf("history command exit=%v stderr=%s", err, stderr.Bytes())
	}
	after := captureObserverServices(t, nodes)
	requireNoError(t, writeStateExportJSON(filepath.Join(output, name+"-state.json"), map[string]json.RawMessage{"Before": before, "After": after}))
	if !bytes.Equal(before, after) {
		t.Fatal("history command changed node state")
	}
	return stdout.Bytes()
}

func captureObserverTruth(t *testing.T, f *fixture, owner common.Address) observerServiceTruth {
	t.Helper()
	head := f.chain.CurrentBlock()
	state, err := f.chain.State()
	requireNoError(t, err)
	all, err := state.AllTickets()
	requireNoError(t, err)
	var tickets map[common.Hash]common.TicketDisplay
	for id, ticket := range all.ToMap() {
		if ticket.Owner == owner {
			if tickets == nil {
				tickets = make(map[common.Hash]common.TicketDisplay)
			}
			tickets[id] = ticket
		}
	}
	return observerServiceTruth{Header: head.Header(), TD: f.chain.GetTd(head.Hash(), head.NumberU64()), Nonce: state.GetNonce(owner), LiquidWei: state.GetBalance(common.SystemAssetID, owner).String(), TimeLocks: state.GetTimeLockBalance(common.SystemAssetID, owner), Tickets: tickets}
}

func requireObserverTruth(t *testing.T, report observe.Report, truth [2]observerServiceTruth) {
	t.Helper()
	if len(report.Nodes) != 2 {
		t.Fatal("expected two observations")
	}
	for i, node := range report.Nodes {
		if node.Identity != "matches" || node.Consistency != "stable" || len(node.Issues) != 0 || node.Head == nil || node.Nonce == nil || node.LiquidWei == nil || node.TimeLocks == nil || node.Head.TotalDifficulty == nil || !node.TicketsKnown || !node.PoolKnown || node.SavedIntent != "unknown" || len(node.Tracked) != 4 {
			t.Fatalf("node %d incomplete: %+v", i, node)
		}
		actual := observerServiceTruth{Header: node.Head.Header, TD: (*big.Int)(node.Head.TotalDifficulty), Nonce: uint64(*node.Nonce), LiquidWei: *node.LiquidWei, TimeLocks: node.TimeLocks, Tickets: node.Tickets}
		if !bytes.Equal(mustObserverJSON(t, actual), mustObserverJSON(t, truth[i])) {
			t.Fatalf("node %d differs from independently prepared state", i)
		}
	}
}

func runServiceObserver(t *testing.T, binary, output, name string, config observe.Config, nodes [2]*rehearsalNode) observe.Report {
	t.Helper()
	before := captureObserverServices(t, nodes)
	path := filepath.Join(output, name+"-config.json")
	requireNoError(t, writeStateExportJSON(path, config))
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary, "--config", path, "--timeout", "5s")
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	requireNoError(t, os.WriteFile(filepath.Join(output, name+".json"), stdout.Bytes(), 0600))
	requireNoError(t, os.WriteFile(filepath.Join(output, name+"-stderr.txt"), stderr.Bytes(), 0600))
	if err != nil || stderr.Len() != 0 {
		t.Fatalf("observer exit=%v stderr=%s", err, stderr.Bytes())
	}
	after := captureObserverServices(t, nodes)
	requireNoError(t, writeStateExportJSON(filepath.Join(output, name+"-state.json"), map[string]json.RawMessage{"Before": before, "After": after}))
	if !bytes.Equal(before, after) {
		t.Fatal("observer invocation changed head, flags, signatures, nonce, saved record or pool")
	}
	var report observe.Report
	requireNoError(t, json.Unmarshal(stdout.Bytes(), &report))
	return report
}

func captureObserverServices(t *testing.T, nodes [2]*rehearsalNode) json.RawMessage {
	t.Helper()
	var result []interface{}
	for _, node := range nodes {
		if node.cmd != nil {
			result = append(result, node.status(t), readPeerPurchase(t, node))
		}
	}
	return mustObserverJSON(t, result)
}

func mustObserverJSON(t *testing.T, value interface{}) []byte {
	t.Helper()
	raw, err := json.Marshal(value)
	requireNoError(t, err)
	return raw
}
