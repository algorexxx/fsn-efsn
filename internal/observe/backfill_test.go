package observe

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func backfillFixture(t *testing.T, branch string) (*retainedRPC, Config, map[string]BlockEvidence) {
	t.Helper()
	config, report := serviceHistoryInput(t, "ipc-divergence", 1)
	config.Nodes = config.Nodes[:1]
	f := &retainedRPC{chainID: "0xd903", networkID: config.NetworkID, blocks: make(map[uint64]map[string]interface{}), receipts: make(map[common.Hash]*types.Receipt), raw: make(map[string]hexutil.Bytes)}
	f.blocks[0] = headerResponse(t, report.Nodes[0].Genesis.Header)
	for _, node := range report.Nodes {
		for _, tracked := range node.Tracked {
			if tracked.Receipt != nil {
				f.receipts[tracked.Hash] = tracked.Receipt
			}
		}
	}
	base := filepath.Join("..", "..", "docs", "evidence", "restart-observer-services-2026-09-27", "attempt-4", "services")
	evidence := make(map[string]BlockEvidence)
	for _, name := range []string{"anchor", "local-25", "remote-25", "remote-26"} {
		raw, err := os.ReadFile(filepath.Join(base, name+".rlp"))
		if err != nil {
			t.Fatal(err)
		}
		var block types.Block
		if err := rlp.DecodeBytes(raw, &block); err != nil {
			t.Fatal(err)
		}
		entry := BlockEvidence{RLP: raw, Receipts: make(types.Receipts, 0, len(block.Transactions()))}
		for i, tx := range block.Transactions() {
			signed, err := tx.MarshalBinary()
			if err != nil {
				t.Fatal(err)
			}
			f.raw[block.Hash().Hex()+":"+hexutil.EncodeUint64(uint64(i))] = signed
			entry.Receipts = append(entry.Receipts, f.receipts[tx.Hash()])
		}
		evidence[name] = entry
		if name == "anchor" || name == branch+"-25" || name == "remote-26" && branch == "remote" {
			setBackfillBlock(t, f, entry)
		}
	}
	if branch == "local" {
		block, err := validateBlockEvidence(evidence["local-25"])
		if err != nil {
			t.Fatal(err)
		}
		f.head = block.Header()
	}
	server := httptest.NewServer(f)
	t.Cleanup(server.Close)
	config.Nodes[0].Endpoint = server.URL
	return f, config, evidence
}

func setBackfillBlock(t *testing.T, f *retainedRPC, entry BlockEvidence) {
	t.Helper()
	var block types.Block
	if err := rlp.DecodeBytes(entry.RLP, &block); err != nil {
		t.Fatal(err)
	}
	response := headerResponse(t, block.Header())
	hashes := make([]common.Hash, 0, len(block.Transactions()))
	for _, tx := range block.Transactions() {
		hashes = append(hashes, tx.Hash())
	}
	response["transactions"], response["uncles"] = hashes, []common.Hash{}
	f.blocks[block.NumberU64()] = response
	f.head = block.Header()
}

func backfillAt(t *testing.T, history *History, config Config, limit uint64, tick int) HistoryStatus {
	t.Helper()
	now := func() time.Time { return time.Date(2026, 9, 27, 20, 0, tick, 0, time.UTC) }
	status, err := history.Backfill(context.Background(), config, config.Nodes[0].Name, limit, 2*time.Second, now)
	if err != nil {
		t.Fatal(err)
	}
	return status
}

func TestBackfillRetainedForkAndResume(t *testing.T) {
	expectedDetails := []string{"previous tip 25:0x2cebfd43780e2db56bfc77dec6240f0100fe0fbab68c3288f235361260c4730d displaced after 24:0xbca984198362614919fc81be99808e8829c40bda9c58114d90405e8d4be919b1"}
	f, config, evidence := backfillFixture(t, "local")
	directory := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(directory, config, 16*1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { history.Close() })
	first := backfillAt(t, history, config, 1, 1)
	if first.Blocks[0].Status != "complete_at_observation" || first.Blocks[0].StoredThrough.Number != 25 || first.Coverage != "bounded_block_history_see_nodes" {
		t.Fatal("initial complete branch not retained", first.Blocks)
	}
	f.mu.Lock()
	setBackfillBlock(t, f, evidence["remote-25"])
	setBackfillBlock(t, f, evidence["remote-26"])
	f.mu.Unlock()
	fork := backfillAt(t, history, config, 1, 2)
	change := findIncident(t, fork, "node-1", "canonical_history_change", common.Hash{})
	if !reflect.DeepEqual(change.Details, expectedDetails) {
		t.Fatalf("canonical-change details: got %q, want %q", change.Details, expectedDetails)
	}
	gap := findIncident(t, fork, "node-1", "block_coverage", common.Hash{})
	if fork.Blocks[0].Status != "batch_limit" || fork.Blocks[0].StoredThrough.Number != 25 || fork.Blocks[0].StoredThrough.Hash == first.Blocks[0].StoredThrough.Hash || fork.Blocks[0].ObservedHead.Number != 26 || change.Status != "open" || gap.Status != "open" {
		t.Fatal("fork or incomplete coverage hidden", fork.Blocks)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	history, err = OpenHistory(directory)
	if err != nil {
		t.Fatal(err)
	}
	resumed := backfillAt(t, history, config, 1, 3)
	if replayed := findIncident(t, resumed, "node-1", "canonical_history_change", common.Hash{}); replayed.ID != change.ID || !reflect.DeepEqual(replayed.Details, expectedDetails) {
		t.Fatal("canonical-change identity or readable details changed after reopening")
	}
	if resumed.Blocks[0].Status != "complete_at_observation" || resumed.Blocks[0].StoredThrough.Number != 26 || findIncident(t, resumed, "node-1", "canonical_history_change", common.Hash{}).Status != "open" || findIncident(t, resumed, "node-1", "block_coverage", common.Hash{}).Observation != "not_observed" {
		t.Fatal("resume failed or automatically resolved incident", resumed.Blocks)
	}
	_, err = history.Review(Review{Action: "resolve", Incident: change.ID, Reason: "Synthetic fork review only."}, 3, time.Date(2026, 9, 27, 20, 0, 4, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	f.mu.Lock()
	setBackfillBlock(t, f, evidence["local-25"])
	f.mu.Unlock()
	rewound := backfillAt(t, history, config, 1, 5)
	if rewound.Blocks[0].StoredThrough != first.Blocks[0].StoredThrough || findIncident(t, rewound, "node-1", "canonical_history_change", common.Hash{}).Occurrences != 2 {
		t.Fatal("shorter competing branch did not reopen reviewed incident")
	}
	var exported bytes.Buffer
	if err := history.Export(&exported); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"local-25", "remote-25", "remote-26"} {
		if !bytes.Contains(exported.Bytes(), []byte(hexutil.Encode(evidence[name].RLP))) {
			t.Fatal("displaced block evidence lost", name)
		}
	}
	if output := os.Getenv("FUSION_BACKFILL_EVIDENCE"); output != "" {
		if err := os.WriteFile(filepath.Join(output, "fork-history.jsonl"), exported.Bytes(), 0600); err != nil {
			t.Fatal(err)
		}
		raw, _ := json.MarshalIndent(rewound, "", "  ")
		if err := os.WriteFile(filepath.Join(output, "fork-status.json"), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestBackfillFailuresDoNotSkipBlocks(t *testing.T) {
	for _, failure := range []string{"missing_receipt", "wrong_raw", "wrong_receipt", "nil_log", "missing_status", "bad_root", "uncles", "missing_body", "head_changes", "missing_block", "wrong_identity", "retired", "timeout"} {
		t.Run(failure, func(t *testing.T) {
			f, config, _ := backfillFixture(t, "remote")
			switch failure {
			case "missing_receipt":
				f.null = "eth_getTransactionReceipt"
			case "wrong_raw":
				f.wrongRaw = true
			case "wrong_receipt":
				f.wrongReceiptHash = true
			case "nil_log":
				f.nilLog = true
			case "missing_status":
				f.missingStatus = true
			case "bad_root":
				f.blocks[25]["transactions"] = []common.Hash{}
			case "uncles":
				f.blocks[25]["uncles"] = []common.Hash{common.HexToHash("0x1")}
			case "missing_body":
				delete(f.blocks[25], "transactions")
			case "head_changes":
				f.changeRead = 2
			case "missing_block":
				delete(f.blocks, 25)
			case "wrong_identity":
				f.networkID = "1"
			case "retired":
				config.Nodes[0].Role = "retired"
			case "timeout":
				f.delay = 50 * time.Millisecond
			}
			history, err := CreateHistory(filepath.Join(t.TempDir(), "history"), config, 1024*1024)
			if err != nil {
				t.Fatal(err)
			}
			defer history.Close()
			timeout := 2 * time.Second
			if failure == "timeout" {
				timeout = time.Millisecond
			}
			state, err := history.Backfill(context.Background(), config, "node-1", 2, timeout, time.Now)
			if err != nil || state.Sequence != 1 || state.Blocks[0].Status == "complete_at_observation" || state.Blocks[0].StoredThrough.Number != 24 {
				t.Fatal("failure advanced coverage", state.Blocks, err)
			}
			if failure == "retired" {
				f.mu.Lock()
				defer f.mu.Unlock()
				if len(f.methods) != 0 {
					t.Fatal("retired node contacted")
				}
			}
		})
	}
}

func TestBackfillBudgetAndSnapshotInvalidation(t *testing.T) {
	_, config, _ := backfillFixture(t, "local")
	history, err := CreateHistory(filepath.Join(t.TempDir(), "small"), config, 1024)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := history.Backfill(context.Background(), config, "node-1", 1, time.Second, time.Now); err == nil {
		t.Fatal("over-budget backfill accepted")
	}
	state, err := history.Status()
	if err != nil || state.Sequence != 0 || len(state.Blocks) != 0 {
		t.Fatal("failed write advanced derived coverage", err)
	}
	history.Close()
	history, err = CreateHistory(filepath.Join(t.TempDir(), "history"), config, 1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	backfillAt(t, history, config, 1, 1)
	_, report := serviceHistoryInput(t, "ipc-divergence", 1)
	report.Nodes = report.Nodes[:1]
	report.StartedUTC = time.Date(2026, 9, 27, 20, 1, 0, 0, time.UTC)
	report.FinishedUTC = report.StartedUTC
	report.Nodes[0].StartedUTC, report.Nodes[0].FinishedUTC = report.StartedUTC, report.StartedUTC
	state, err = history.Record(config, report)
	if err != nil || state.Blocks[0].Status != "not_rechecked" || state.Blocks[0].StoredThrough.Number != 25 {
		t.Fatal("snapshot pretended to refresh block history", err)
	}
}

func TestBackfillPartialGapThenRetry(t *testing.T) {
	f, config, evidence := backfillFixture(t, "remote")
	delete(f.blocks[26], "transactions")
	history, err := CreateHistory(filepath.Join(t.TempDir(), "history"), config, 1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	partial := backfillAt(t, history, config, 2, 1)
	if partial.Blocks[0].StoredThrough.Number != 25 || partial.Blocks[0].Status != "block_unavailable_or_invalid" || partial.Blocks[0].ObservedHead.Number != 26 {
		t.Fatal("valid prefix lost or missing next block skipped", partial.Blocks)
	}
	f.mu.Lock()
	setBackfillBlock(t, f, evidence["remote-26"])
	f.mu.Unlock()
	complete := backfillAt(t, history, config, 2, 2)
	if complete.Blocks[0].StoredThrough.Number != 26 || complete.Blocks[0].Status != "complete_at_observation" {
		t.Fatal("retry did not fill missing block", complete.Blocks)
	}
}

func TestBlockEvidenceRejectsTampering(t *testing.T) {
	_, _, evidence := backfillFixture(t, "local")
	for _, change := range []string{"receipt_root", "receipt_bloom", "log_index", "gas", "missing_receipt", "transaction_root", "parent_link"} {
		t.Run(change, func(t *testing.T) {
			raw, _ := json.Marshal(evidence["local-25"])
			var entry BlockEvidence
			if err := json.Unmarshal(raw, &entry); err != nil {
				t.Fatal(err)
			}
			switch change {
			case "receipt_root":
				entry.Receipts[0].Status = 0
			case "receipt_bloom":
				entry.Receipts[0].Bloom = types.Bloom{}
			case "log_index":
				entry.Receipts[0].Logs[0].Index++
			case "gas":
				entry.Receipts[0].GasUsed++
			case "missing_receipt":
				entry.Receipts = nil
			case "transaction_root", "parent_link":
				var block types.Block
				if err := rlp.DecodeBytes(entry.RLP, &block); err != nil {
					t.Fatal(err)
				}
				modified := types.NewBlockWithHeader(block.Header())
				if change == "parent_link" {
					header := block.Header()
					header.ParentHash = common.HexToHash("0x1")
					modified = types.NewBlockWithHeader(header).WithBody(block.Transactions(), nil)
				}
				entry.RLP, _ = rlp.EncodeToBytes(modified)
			}
			if _, err := validateBlockEvidence(entry); err == nil {
				t.Fatal("tampered complete evidence accepted")
			}
		})
	}
}

func TestBackfillReplayRejectsBrokenContinuity(t *testing.T) {
	_, config, evidence := backfillFixture(t, "local")
	history, err := CreateHistory(filepath.Join(t.TempDir(), "history"), config, 1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	first := backfillAt(t, history, config, 1, 1)
	_, remoteConfig, _ := backfillFixture(t, "remote")
	state, err := history.load()
	if err != nil {
		t.Fatal(err)
	}
	now := func() time.Time { return time.Date(2026, 9, 27, 20, 0, 2, 0, time.UTC) }
	report := collectBackfill(context.Background(), remoteConfig, remoteConfig.Nodes[0], []common.Hash{config.AnchorHash}, 2, now)
	report.Base = &first.Blocks[0].StoredThrough
	report.Blocks = []BlockEvidence{evidence["remote-26"]}
	if _, err := history.append(state, historyEvent{Sequence: 2, TimeUTC: now(), Backfill: &report}); err == nil {
		t.Fatal("disconnected replacement passed history replay")
	}
	after, err := history.Status()
	if err != nil || after.Sequence != 1 || after.Blocks[0].StoredThrough != first.Blocks[0].StoredThrough {
		t.Fatal("rejected event changed persistent coverage", err)
	}
}
