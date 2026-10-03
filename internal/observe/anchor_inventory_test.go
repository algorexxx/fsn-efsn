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
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func anchorInventoryFixture(t *testing.T) (*retainedRPC, Config, []historyEvent) {
	t.Helper()
	config, events := miningTicketFixture(t)
	anchor := events[0].Report.Nodes[0].Head
	f := &retainedRPC{chainID: "0xd903", networkID: config.NetworkID, blocks: make(map[uint64]map[string]interface{}), tickets: make(map[uint64]map[common.Hash]common.TicketDisplay)}
	f.blocks[0] = headerResponse(t, events[0].Report.Nodes[0].Genesis.Header)
	f.blocks[config.AnchorNumber] = headerResponse(t, anchor.Header)
	f.tickets[config.AnchorNumber] = make(map[common.Hash]common.TicketDisplay)
	for _, node := range events[0].Report.Nodes {
		for id, ticket := range node.Tickets {
			f.tickets[config.AnchorNumber][id] = ticket
		}
	}
	for _, event := range events {
		if event.Backfill == nil {
			continue
		}
		for _, evidence := range event.Backfill.Blocks {
			setBackfillBlock(t, f, evidence)
		}
	}
	for i := range events[0].Report.Nodes {
		events[0].Report.Nodes[i].TicketsKnown = false
	}
	server := httptest.NewServer(f)
	t.Cleanup(server.Close)
	config.Nodes[1].Endpoint = server.URL
	return f, config, events
}

func TestAnchorInventoryAfterBackfill(t *testing.T) {
	f, config, events := anchorInventoryFixture(t)
	history, directory := ticketHistory(t, config, events)
	expected := events[0].Report.Nodes[1].Tickets
	expectedFinal := expectedTicketInventory(t, 29, donation)
	now := func() time.Time { return events[len(events)-1].TimeUTC.Add(time.Second) }
	before, err := history.Status()
	if err != nil {
		t.Fatal(err)
	}
	missing, err := history.TicketTimeline("node-2", 0, 128)
	if err != nil || missing.Status != "missing_baseline" {
		t.Fatal("baseline fixture was already seeded", err)
	}

	report, err := history.CollectAnchorInventory(context.Background(), config, "node-2", time.Second, now)
	after, statusErr := history.Status()
	timeline, timelineErr := history.TicketTimeline("node-2", 0, 128)

	if err != nil || statusErr != nil || timelineErr != nil || report.Status != "ready" || !reflect.DeepEqual(report.Tickets, expected) || f.head.Number.Uint64() != 29 || timeline.Status != "complete_for_retained_prefix" || timeline.BaselineSequence != 11 || !reflect.DeepEqual(timeline.Inventory, expectedFinal) {
		t.Fatalf("historical baseline failed: %v %v %v %+v", err, statusErr, timelineErr, report)
	}
	if !reflect.DeepEqual(before.Blocks, after.Blocks) || !reflect.DeepEqual(before.Incidents, after.Incidents) || before.LastReportUTC != after.LastReportUTC || after.Sequence != before.Sequence+1 {
		t.Fatal("baseline changed live coverage or incidents")
	}
	f.mu.Lock()
	methods := append([]string(nil), f.methods...)
	f.mu.Unlock()
	if !reflect.DeepEqual(methods, []string{"eth_chainId", "net_version", "eth_getBlockByNumber", "eth_getBlockByNumber", "fsn_allTicketsByAddress", "eth_getBlockByNumber"}) {
		t.Fatal("unexpected historical read methods", methods)
	}
	var original bytes.Buffer
	if err := history.Export(&original); err != nil {
		t.Fatal(err)
	}
	if output := os.Getenv("FUSION_ANCHOR_EVIDENCE"); output != "" {
		for name, value := range map[string]interface{}{"inventory": report, "timeline": timeline} {
			raw, err := json.MarshalIndent(value, "", "  ")
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(output, name+".json"), raw, 0600); err != nil {
				t.Fatal(err)
			}
		}
		if err := os.WriteFile(filepath.Join(output, "history.jsonl"), original.Bytes(), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := OpenHistory(directory)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	cold, err := reopened.TicketTimeline("node-2", 0, 128)
	var exported bytes.Buffer
	exportErr := reopened.Export(&exported)
	if err != nil || exportErr != nil || !reflect.DeepEqual(cold, timeline) || !bytes.Equal(original.Bytes(), exported.Bytes()) {
		t.Fatal("cold baseline derivation differs", err, exportErr)
	}
}

func TestAnchorInventoryFailureAndEmptyResults(t *testing.T) {
	for _, test := range []struct{ change, status string }{{"pruned", "unavailable"}, {"empty", "ready"}, {"identity", "identity_mismatch"}, {"wrong_anchor", "identity_mismatch"}, {"anchor_changed", "unstable"}, {"height", "invalid_inventory"}, {"value", "invalid_inventory"}, {"retired", "retired"}, {"deadline", "unavailable"}} {
		t.Run(test.change, func(t *testing.T) {
			f, config, events := anchorInventoryFixture(t)
			timeout := time.Second
			switch test.change {
			case "pruned":
				f.fail = "fsn_allTicketsByAddress"
			case "empty":
				f.tickets[config.AnchorNumber] = nil
			case "identity":
				f.chainID = "0x1"
			case "wrong_anchor":
				header := types.CopyHeader(events[0].Report.Nodes[0].Head.Header)
				header.Time++
				f.blocks[config.AnchorNumber] = headerResponse(t, header)
			case "anchor_changed":
				f.head, f.changeRead = events[0].Report.Nodes[0].Head.Header, 2
			case "retired":
				config.Nodes[1].Role = "retired"
			case "deadline":
				f.delay, timeout = 50*time.Millisecond, 5*time.Millisecond
			default:
				for id, ticket := range f.tickets[config.AnchorNumber] {
					if ticket.Owner != donation {
						continue
					}
					switch test.change {
					case "height":
						ticket.Height = config.AnchorNumber + 1
					case "value":
						ticket.Value = nil
					}
					f.tickets[config.AnchorNumber][id] = ticket
					break
				}
			}
			history, _ := ticketHistory(t, config, events)
			now := func() time.Time { return events[len(events)-1].TimeUTC.Add(time.Second) }

			report, err := history.CollectAnchorInventory(context.Background(), config, "node-2", timeout, now)

			if err != nil || report.Status != test.status || test.status != "ready" && report.Tickets != nil || test.change == "empty" && (report.Tickets == nil || len(report.Tickets) != 0) {
				t.Fatalf("unexpected historical outcome: %v %+v", err, report)
			}
			if test.change == "retired" && len(f.methods) != 0 {
				t.Fatal("retired endpoint contacted")
			}
		})
	}
}

func TestAnchorInventoryConflictsRemainVisible(t *testing.T) {
	f, config, events := anchorInventoryFixture(t)
	history, _ := ticketHistory(t, config, events)
	tick := events[len(events)-1].TimeUTC
	now := func() time.Time { tick = tick.Add(time.Second); return tick }
	if _, err := history.CollectAnchorInventory(context.Background(), config, "node-2", time.Second, now); err != nil {
		t.Fatal(err)
	}
	f.mu.Lock()
	f.fail = "fsn_allTicketsByAddress"
	f.mu.Unlock()
	if _, err := history.CollectAnchorInventory(context.Background(), config, "node-2", time.Second, now); err != nil {
		t.Fatal(err)
	}
	valid, err := history.TicketTimeline("node-2", 0, 128)
	if err != nil || valid.Status != "complete_for_retained_prefix" {
		t.Fatal("failed later read erased baseline", err)
	}
	f.mu.Lock()
	f.fail = ""
	for id, ticket := range f.tickets[config.AnchorNumber] {
		if ticket.Owner == donation {
			delete(f.tickets[config.AnchorNumber], id)
			break
		}
	}
	f.mu.Unlock()
	if _, err := history.CollectAnchorInventory(context.Background(), config, "node-2", time.Second, now); err != nil {
		t.Fatal(err)
	}

	conflict, err := history.TicketTimeline("node-2", 0, 128)

	if err != nil || conflict.Status != "conflicting_baseline" || conflict.Inventory != nil || conflict.Through != nil {
		t.Fatal("contradictory historical baseline silently replaced", err)
	}
}

func TestAnchorInventoryReplayValidation(t *testing.T) {
	_, config, events := anchorInventoryFixture(t)
	for _, change := range []string{"owner", "nil_tickets", "anchor_after", "wallet", "unknown_status", "failed_with_tickets", "time"} {
		t.Run(change, func(t *testing.T) {
			_, source := miningTicketFixture(t)
			node := source[0].Report.Nodes[1]
			report := AnchorInventory{Node: node.Name, Wallet: node.Wallet, StartedUTC: node.StartedUTC, FinishedUTC: node.FinishedUTC, ChainID: node.ChainID, NetworkID: node.NetworkID, Genesis: node.Genesis, Anchor: node.Anchor, AnchorAfter: node.Anchor, Tickets: node.Tickets, Status: "ready"}
			switch change {
			case "owner":
				for id, ticket := range report.Tickets {
					ticket.Owner = common.Address{}
					report.Tickets[id] = ticket
					break
				}
			case "nil_tickets":
				report.Tickets = nil
			case "anchor_after":
				report.AnchorAfter = nil
			case "wallet":
				report.Wallet = common.Address{}
			case "unknown_status":
				report.Status = "invented"
			case "failed_with_tickets":
				report.Status = "unavailable"
			case "time":
				report.FinishedUTC = report.StartedUTC.Add(-time.Second)
			}

			err := validateAnchorInventory(scopeFor(config), &report)

			if err == nil {
				t.Fatal("invalid persisted anchor evidence accepted", change)
			}
		})
	}
	history, _ := ticketHistory(t, config, events)
	for _, name := range []string{"missing", "node-2"} {
		timeout := time.Second
		if name == "node-2" {
			timeout = 0
		}
		if _, err := history.CollectAnchorInventory(context.Background(), config, name, timeout, time.Now); err == nil {
			t.Fatal("invalid acquisition accepted")
		}
	}
}

func TestAnchorInventoryBudgetFailurePreservesHistory(t *testing.T) {
	_, config, events := anchorInventoryFixture(t)
	history, err := CreateHistory(filepath.Join(t.TempDir(), "history"), config, 1024)
	if err != nil {
		t.Fatal(err)
	}
	defer history.Close()
	var before bytes.Buffer
	if err := history.Export(&before); err != nil {
		t.Fatal(err)
	}
	now := func() time.Time { return events[0].TimeUTC }

	_, collectionErr := history.CollectAnchorInventory(context.Background(), config, "node-2", time.Second, now)
	var after bytes.Buffer
	exportErr := history.Export(&after)

	if collectionErr == nil || exportErr != nil || !bytes.Equal(before.Bytes(), after.Bytes()) {
		t.Fatal("failed append altered history", collectionErr, exportErr)
	}
}
