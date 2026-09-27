package observe

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func miningTicketFixture(t *testing.T) (Config, []historyEvent) {
	t.Helper()
	base := filepath.Join("..", "..", "docs", "evidence", "restart-observer-mining-2026-09-27", "attempt-3", "mining")
	var config Config
	readFixture(t, filepath.Join(base, "ipc-config.json"), &config)
	for i := range config.Nodes {
		config.Nodes[i].Endpoint = fmt.Sprintf("http://node-%d.invalid", i)
	}
	file, err := os.Open(filepath.Join(base, "cold-history-export.jsonl"))
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	var metadata json.RawMessage
	if err := decoder.Decode(&metadata); err != nil {
		t.Fatal(err)
	}
	var events []historyEvent
	for {
		var event historyEvent
		err := decoder.Decode(&event)
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		events = append(events, event)
	}
	return config, events
}

func ticketHistory(t *testing.T, config Config, events []historyEvent) (*History, string) {
	t.Helper()
	directory := filepath.Join(t.TempDir(), "history")
	history, err := CreateHistory(directory, config, 16*1024*1024)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { history.Close() })
	state, err := history.load()
	if err != nil {
		t.Fatal(err)
	}
	for _, event := range events {
		if _, err := history.append(state, event); err != nil {
			t.Fatal(err)
		}
	}
	return history, directory
}

func expectedTicketInventory(t *testing.T, height uint64, wallet common.Address) map[common.Hash]common.TicketDisplay {
	t.Helper()
	var ledger struct {
		Tickets map[common.Hash]common.TicketDisplay
	}
	readFixture(t, filepath.Join("..", "..", "docs", "evidence", "restart-observer-mining-2026-09-27", "attempt-3", "mining", fmt.Sprintf("ledger-%d.json", height)), &ledger)
	result := make(map[common.Hash]common.TicketDisplay)
	for id, ticket := range ledger.Tickets {
		if ticket.Owner == wallet {
			result[id] = ticket
		}
	}
	return result
}

func expectedTicketEvents(t *testing.T, wallet common.Address, from, through uint64) []TicketEvent {
	t.Helper()
	var recorded []struct {
		Block          common.Hash
		Height         uint64
		Kind           string
		Transaction    common.Hash
		TicketID       common.Hash
		Ticket         common.TicketDisplay
		RetreatIndex   int
		ReturnExpected bool
	}
	readFixture(t, filepath.Join("..", "..", "docs", "evidence", "restart-observer-mining-2026-09-27", "attempt-3", "mining", "native-events.json"), &recorded)
	result := []TicketEvent{}
	for _, record := range recorded {
		if record.Ticket.Owner != wallet || record.Height < from || record.Height > through {
			continue
		}
		ticket := record.Ticket
		event := TicketEvent{Block: BlockReference{Number: record.Height, Hash: record.Block}, Kind: record.Kind, Transaction: record.Transaction, TicketID: record.TicketID, Ticket: &ticket}
		if record.ReturnExpected {
			event.Return = "interval_rights"
		}
		if record.Kind == "retreat" {
			index := record.RetreatIndex
			event.RetreatIndex, event.Return = &index, "none_first_retreat"
		}
		result = append(result, event)
	}
	return result
}

func TestTicketTimelineRetainedMiningAndColdRead(t *testing.T) {
	config, events := miningTicketFixture(t)
	history, directory := ticketHistory(t, config, events)
	var before bytes.Buffer
	if err := history.Export(&before); err != nil {
		t.Fatal(err)
	}
	for _, node := range config.Nodes {
		expectedInventory := expectedTicketInventory(t, 29, node.Wallet)
		expectedEvents := expectedTicketEvents(t, node.Wallet, 25, 29)

		timeline, err := history.TicketTimeline(node.Name, 0, 128)

		if err != nil || timeline.Status != "complete_for_retained_prefix" || timeline.Through == nil || timeline.Through.Number != 29 || timeline.Through.Hash != common.HexToHash("0x7ac9a79e964f18731c9182fd1a40565d540fe4b40f897dae5d975da8bb79598d") || timeline.BaselineSequence != 1 || timeline.Sequence != uint64(len(events)) || !reflect.DeepEqual(timeline.Inventory, expectedInventory) || !reflect.DeepEqual(timeline.Events, expectedEvents) {
			t.Fatalf("retained mining ledger differs: %v %+v", err, timeline)
		}
		if output := os.Getenv("FUSION_TICKET_EVIDENCE"); output != "" {
			raw, err := json.MarshalIndent(timeline, "", "  ")
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(output, node.Name+".json"), raw, 0600); err != nil {
				t.Fatal(err)
			}
		}
	}
	first, err := history.TicketTimeline("node-2", 0, 128)
	if err != nil {
		t.Fatal(err)
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := OpenHistory(directory)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	second, err := reopened.TicketTimeline("node-2", 0, 128)
	var after bytes.Buffer
	exportErr := reopened.Export(&after)
	if err != nil || exportErr != nil || !reflect.DeepEqual(first, second) || !bytes.Equal(before.Bytes(), after.Bytes()) {
		t.Fatal("offline/cold derivation changed immutable history or result", err, exportErr)
	}
}

func TestTicketTimelineRangeAndScope(t *testing.T) {
	config, events := miningTicketFixture(t)
	history, _ := ticketHistory(t, config, events)
	for _, test := range []struct {
		from, count, through uint64
		status               string
	}{{27, 2, 28, "range_limit"}, {30, 1, 29, "range_not_retained"}, {25, 1, 25, "range_limit"}} {
		expectedInventory := expectedTicketInventory(t, test.through, config.Nodes[1].Wallet)
		expectedEvents := expectedTicketEvents(t, config.Nodes[1].Wallet, test.from, test.through)

		timeline, err := history.TicketTimeline("node-2", test.from, test.count)

		if err != nil || timeline.Status != test.status || timeline.Through == nil || timeline.Through.Number != test.through || !reflect.DeepEqual(timeline.Inventory, expectedInventory) || !reflect.DeepEqual(timeline.Events, expectedEvents) {
			t.Fatalf("range does not replay prefix: %v %+v", err, timeline)
		}
	}
	for _, test := range []struct {
		node        string
		from, count uint64
	}{{"missing", 25, 1}, {"node-2", 24, 1}, {"node-2", 25, 0}, {"node-2", 25, 129}, {"node-2", ^uint64(0), 2}} {
		if _, err := history.TicketTimeline(test.node, test.from, test.count); err == nil {
			t.Fatal("invalid range or scope accepted", test)
		}
	}
}

func TestTicketTimelineBaselineGaps(t *testing.T) {
	for _, test := range []struct{ change, status string }{{"unknown", "missing_baseline"}, {"unstable", "missing_baseline"}, {"identity", "missing_baseline"}, {"later", "missing_baseline"}, {"nil", "invalid_baseline"}, {"owner", "invalid_baseline"}, {"value", "invalid_baseline"}, {"interval", "invalid_baseline"}, {"height", "invalid_baseline"}, {"conflict", "conflicting_baseline"}} {
		t.Run(test.change, func(t *testing.T) {
			config, events := miningTicketFixture(t)
			node := &events[0].Report.Nodes[1]
			switch test.change {
			case "unknown":
				node.TicketsKnown = false
			case "unstable":
				node.Consistency = "changed"
			case "identity":
				node.Identity = "unknown"
			case "later":
				block, err := validateBlockEvidence(events[1].Backfill.Blocks[0])
				if err != nil {
					t.Fatal(err)
				}
				node.Head = &Block{Header: block.Header(), Hash: block.Hash()}
			case "nil":
				node.Tickets = nil
			case "conflict":
				var duplicate historyEvent
				raw, _ := json.Marshal(events[0])
				if err := json.Unmarshal(raw, &duplicate); err != nil {
					t.Fatal(err)
				}
				for id := range duplicate.Report.Nodes[1].Tickets {
					delete(duplicate.Report.Nodes[1].Tickets, id)
					break
				}
				duplicate.Sequence = 2
				duplicate.Report.StartedUTC = duplicate.TimeUTC
				for i := range duplicate.Report.Nodes {
					duplicate.Report.Nodes[i].StartedUTC, duplicate.Report.Nodes[i].FinishedUTC = duplicate.TimeUTC, duplicate.TimeUTC
				}
				events = []historyEvent{events[0], duplicate}
			default:
				for id, ticket := range node.Tickets {
					switch test.change {
					case "owner":
						ticket.Owner = config.Nodes[0].Wallet
					case "value":
						ticket.Value = nil
					case "interval":
						ticket.StartTime = ticket.ExpireTime
					case "height":
						ticket.Height = 25
					}
					node.Tickets[id] = ticket
					break
				}
			}
			history, _ := ticketHistory(t, config, events)

			timeline, err := history.TicketTimeline("node-2", 0, 128)

			if err != nil || timeline.Status != test.status || timeline.Through != nil || timeline.Inventory != nil || len(timeline.Events) != 0 {
				t.Fatalf("gap hidden: %v %+v", err, timeline)
			}
		})
	}
}

func TestTicketTimelineRewindAndReextension(t *testing.T) {
	config, events := miningTicketFixture(t)
	history, _ := ticketHistory(t, config, events)
	var original bytes.Buffer
	if err := history.Export(&original); err != nil {
		t.Fatal(err)
	}
	var evidence []BlockEvidence
	var report BackfillReport
	for _, event := range events {
		if event.Backfill != nil && event.Backfill.Node == "node-2" {
			report = *event.Backfill
			evidence = append(evidence, report.Blocks...)
		}
	}
	state, err := history.load()
	if err != nil {
		t.Fatal(err)
	}
	report.StartedUTC, report.FinishedUTC = state.LastEventUTC.Add(time.Second), state.LastEventUTC.Add(time.Second)
	report.Base = &BlockReference{Number: config.AnchorNumber, Hash: config.AnchorHash}
	report.Head, report.Blocks, report.Status = report.Anchor, nil, "complete_at_observation"
	if _, err := history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, Backfill: &report}); err != nil {
		t.Fatal(err)
	}

	rewound, err := history.TicketTimeline("node-2", 0, 128)

	if err != nil || rewound.Status != "range_not_retained" || rewound.Through.Number != 24 || !reflect.DeepEqual(rewound.Inventory, events[0].Report.Nodes[1].Tickets) || len(rewound.Events) != 0 {
		t.Fatalf("rewind retained displaced accounting: %v %+v", err, rewound)
	}
	report.StartedUTC, report.FinishedUTC = state.LastEventUTC.Add(time.Second), state.LastEventUTC.Add(time.Second)
	last, err := validateBlockEvidence(evidence[len(evidence)-1])
	if err != nil {
		t.Fatal(err)
	}
	report.Head, report.Blocks, report.MaxBlocks = &Block{Header: last.Header(), Hash: last.Hash()}, evidence, 128
	if _, err := history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, Backfill: &report}); err != nil {
		t.Fatal(err)
	}
	expectedInventory := expectedTicketInventory(t, 29, config.Nodes[1].Wallet)
	expectedEvents := expectedTicketEvents(t, config.Nodes[1].Wallet, 25, 29)

	restored, err := history.TicketTimeline("node-2", 0, 128)
	var extended bytes.Buffer
	exportErr := history.Export(&extended)

	if err != nil || exportErr != nil || restored.Status != "complete_for_retained_prefix" || !reflect.DeepEqual(restored.Inventory, expectedInventory) || !reflect.DeepEqual(restored.Events, expectedEvents) || !bytes.HasPrefix(extended.Bytes(), original.Bytes()) {
		t.Fatal("reextension lost original evidence or inventory", err, exportErr)
	}
}

func TestTicketTimelineBranchReplacement(t *testing.T) {
	config, events := miningTicketFixture(t)
	history, _ := ticketHistory(t, config, events)
	block, receipts := ticketBlockFixture(t, 25)
	header := block.Header()
	header.Time++
	replacement := types.NewBlockWithHeader(header).WithBody(block.Transactions(), nil)
	raw, err := rlp.EncodeToBytes(replacement)
	if err != nil {
		t.Fatal(err)
	}
	state, err := history.load()
	if err != nil {
		t.Fatal(err)
	}
	var report BackfillReport
	for _, event := range events {
		if event.Backfill != nil && event.Backfill.Node == "node-2" {
			report = *event.Backfill
		}
	}
	report.StartedUTC, report.FinishedUTC = state.LastEventUTC.Add(time.Second), state.LastEventUTC.Add(time.Second)
	report.Base = &BlockReference{Number: config.AnchorNumber, Hash: config.AnchorHash}
	report.Head = &Block{Header: replacement.Header(), Hash: replacement.Hash()}
	report.Blocks, report.MaxBlocks, report.Status = []BlockEvidence{{RLP: raw, Receipts: receipts}}, 1, "complete_at_observation"
	if _, err := history.append(state, historyEvent{Sequence: state.Sequence + 1, TimeUTC: report.FinishedUTC, Backfill: &report}); err != nil {
		t.Fatal(err)
	}
	expectedInventory := expectedTicketInventory(t, 25, donation)
	expectedEvents := expectedTicketEvents(t, donation, 25, 25)
	expectedEvents[0].Block.Hash = replacement.Hash()

	timeline, err := history.TicketTimeline("node-2", 0, 128)

	if err != nil || timeline.Through == nil || timeline.Through.Hash != replacement.Hash() || !reflect.DeepEqual(timeline.Inventory, expectedInventory) || !reflect.DeepEqual(timeline.Events, expectedEvents) {
		t.Fatalf("replaced branch still contributes accounting: %v %+v", err, timeline)
	}
}

func TestTicketTimelineStopsBeforeUnsupportedBlock(t *testing.T) {
	config, events := miningTicketFixture(t)
	selection := expectedTicketEvents(t, donation, 26, 26)[1]
	delete(events[0].Report.Nodes[1].Tickets, selection.TicketID)
	history, _ := ticketHistory(t, config, events)
	expectedInventory := expectedTicketInventory(t, 25, donation)
	delete(expectedInventory, selection.TicketID)
	expectedEvents := expectedTicketEvents(t, donation, 25, 25)

	timeline, err := history.TicketTimeline("node-2", 0, 128)

	if err != nil || timeline.Status != "incomplete" || timeline.Issue == "" || timeline.Through == nil || timeline.Through.Number != 25 || !reflect.DeepEqual(timeline.Inventory, expectedInventory) || !reflect.DeepEqual(timeline.Events, expectedEvents) {
		t.Fatalf("incomplete inventory published partial block: %v %+v", err, timeline)
	}
}
