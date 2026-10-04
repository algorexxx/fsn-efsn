package observe

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math/big"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type historyBacklogSample struct {
	Blocks       uint64
	Height       uint64
	LogicalBytes int64
	Operations   []historyCostOperation
}

type historyBacklogResult struct {
	Samples              []historyBacklogSample
	Batches              []historyCostOperation
	ForkOperation        historyCostOperation
	FinalStatus          HistoryStatus
	RestoredStatus       HistoryStatus
	CopiedFiles          int
	CopiedBytes          int64
	ExportSHA256         string
	RestoredExportSHA256 string
	RestoredTimeline     TicketTimeline
	DisplacedBlocks      int
	RPCMethods           map[string]int
}

type closedBacklogCopy struct {
	Files int
	Bytes int64
}

func TestHistoryBoundedBacklogAndClosedCopy(t *testing.T) {
	output := os.Getenv("FUSION_HISTORY_BACKLOG_EVIDENCE")
	if output == "" {
		t.Skip("requires an explicit evidence file for the 4096-block observer fixture")
	}
	if !filepath.IsAbs(output) {
		t.Fatal("absolute new evidence file required")
	}
	config, events := miningTicketFixture(t)
	history, directory := ticketHistory(t, config, events)
	fixture := backlogRPC(t, events)
	server := httptest.NewServer(fixture)
	defer server.Close()
	config.Nodes[1].Endpoint = server.URL
	expectedInventory := expectedTicketInventory(t, 29, config.Nodes[1].Wallet)
	parent, _ := ticketBlockFixture(t, 29)
	blocks := map[uint64]*types.Block{29: parent}
	for number := uint64(30); number <= 4125; number++ {
		parent = addBacklogBlock(t, fixture, parent, 0)
		blocks[number] = parent
	}
	status, err := history.Status()
	if err != nil {
		t.Fatal(err)
	}
	clock := status.LastEventUTC
	now := func() time.Time { return clock }
	result := historyBacklogResult{RPCMethods: make(map[string]int)}
	for _, sample := range []struct{ count, height, from uint64 }{{128, 157, 30}, {1024, 1053, 926}, {4096, 4125, 3998}} {
		fixture.mu.Lock()
		fixture.head = blocks[sample.height].Header()
		fixture.mu.Unlock()
		for status.Blocks[1].StoredThrough.Number < sample.height {
			clock = clock.Add(time.Second)
			result.Batches = append(result.Batches, measureHistoryCost(t, "http_backfill_128", func() error {
				status, err = history.Backfill(context.Background(), config, "node-2", 128, 10*time.Second, now)
				return err
			}))
			coverage := status.Blocks[1]
			if coverage.Status != "batch_limit" && coverage.Status != "complete_at_observation" {
				t.Fatal("bounded backlog did not advance", coverage)
			}
		}
		measured := historyBacklogSample{Blocks: sample.count, Height: sample.height, LogicalBytes: status.LogicalBytes}
		for repeat := 0; repeat < 3; repeat++ {
			measured.Operations = append(measured.Operations, measureBacklogTimeline(t, history, sample.from, sample.height, expectedInventory))
		}
		result.Samples = append(result.Samples, measured)
	}
	before := exportBacklog(t, history)
	parent = blocks[4061]
	fixture.mu.Lock()
	for number := uint64(4062); number <= 4125; number++ {
		parent = addBacklogBlock(t, fixture, parent, 1)
	}
	fixture.mu.Unlock()
	clock = clock.Add(time.Second)
	result.ForkOperation = measureHistoryCost(t, "http_replace_64", func() error {
		status, err = history.Backfill(context.Background(), config, "node-2", 128, 10*time.Second, now)
		return err
	})
	change := findIncident(t, status, "node-2", "canonical_history_change", common.Hash{})
	if status.Blocks[1].StoredThrough.Number != 4125 || status.Blocks[1].StoredThrough.Hash != parent.Hash() || change.Status != "open" {
		t.Fatal("replacement did not retain the new branch and open incident")
	}
	clock = clock.Add(time.Second)
	status, err = history.Review(Review{Action: "acknowledge", Incident: change.ID, Reason: "Bounded synthetic replacement reviewed; unresolved."}, status.Sequence, clock)
	if err != nil {
		t.Fatal(err)
	}
	var expectedTimeline TicketTimeline
	expectedTimeline, err = history.TicketTimeline("node-2", 3998, 128)
	if err != nil || !reflect.DeepEqual(expectedTimeline.Inventory, expectedInventory) || len(expectedTimeline.Events) != 0 || expectedTimeline.Through.Hash != parent.Hash() {
		t.Fatal("replacement changed scoped ticket accounting", err)
	}
	exported := exportBacklog(t, history)
	if !bytes.HasPrefix(exported, before) {
		t.Fatal("replacement rewrote retained evidence")
	}
	for number := uint64(4062); number <= 4125; number++ {
		raw, err := rlp.EncodeToBytes(blocks[number])
		if err != nil || !bytes.Contains(exported, []byte(hexutil.Encode(raw))) {
			t.Fatal("displaced block missing", number, err)
		}
		result.DisplacedBlocks++
	}
	if err := history.Close(); err != nil {
		t.Fatal(err)
	}
	destination := filepath.Join(t.TempDir(), "restored")
	copied := copyClosedBacklog(t, directory, destination)
	result.CopiedFiles, result.CopiedBytes = copied.Files, copied.Bytes
	restored, err := OpenHistory(destination)
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	result.FinalStatus = status
	result.RestoredStatus, err = restored.Status()
	if err != nil {
		t.Fatal(err)
	}
	result.RestoredTimeline, err = restored.TicketTimeline("node-2", 3998, 128)
	restoredExport := exportBacklog(t, restored)
	if err != nil || !reflect.DeepEqual(result.RestoredStatus, status) || !reflect.DeepEqual(result.RestoredTimeline, expectedTimeline) || !bytes.Equal(restoredExport, exported) {
		t.Fatal("closed-copy restore changed status, review, baseline, timeline or evidence", err)
	}
	if review := findIncident(t, result.RestoredStatus, "node-2", "canonical_history_change", common.Hash{}); review.Status != "acknowledged" || review.LastReview.Action != "acknowledge" || review.ID != change.ID {
		t.Fatal("restoration lost unresolved incident identity or acknowledgement")
	}
	result.ExportSHA256 = fmt.Sprintf("%x", sha256.Sum256(exported))
	result.RestoredExportSHA256 = fmt.Sprintf("%x", sha256.Sum256(restoredExport))
	fixture.mu.Lock()
	for _, method := range fixture.methods {
		result.RPCMethods[method]++
	}
	fixture.mu.Unlock()
	encoded, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	file, err := os.OpenFile(output, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		t.Fatal(err)
	}
	_, writeErr := file.Write(append(encoded, '\n'))
	closeErr := file.Close()
	if writeErr != nil || closeErr != nil {
		t.Fatal(writeErr, closeErr)
	}
}

func backlogRPC(t *testing.T, events []historyEvent) *retainedRPC {
	t.Helper()
	report := events[0].Report
	fixture := &retainedRPC{chainID: "0xd903", networkID: "99032659", blocks: make(map[uint64]map[string]interface{}), receipts: make(map[common.Hash]*types.Receipt), raw: make(map[string]hexutil.Bytes)}
	fixture.blocks[0] = headerResponse(t, report.Nodes[1].Genesis.Header)
	fixture.blocks[24] = headerResponse(t, report.Nodes[1].Head.Header)
	for _, event := range events {
		if event.Backfill == nil || event.Backfill.Node != "node-2" {
			continue
		}
		fixture.networkID = *event.Backfill.NetworkID
		for _, entry := range event.Backfill.Blocks {
			setBackfillBlock(t, fixture, entry)
		}
	}
	return fixture
}

func addBacklogBlock(t *testing.T, fixture *retainedRPC, parent *types.Block, branch byte) *types.Block {
	t.Helper()
	number := parent.NumberU64() + 1
	foreign := common.HexToAddress("0x0000000000000000000000000000000000000099")
	data := make([]byte, 37)
	binary.BigEndian.PutUint32(data, 100000)
	data[35], data[36] = 99, 1
	data = append(data, crypto.Keccak256(data)[0])
	header := parent.Header()
	header.ParentHash, header.Number, header.Time = parent.Hash(), new(big.Int).SetUint64(number), parent.Time()+1
	header.Coinbase, header.GasUsed = foreign, 21000
	header.Extra = append(append(make([]byte, 32), data...), make([]byte, 65)...)
	tx := types.NewTransaction(number, foreign, big.NewInt(0), 21000, big.NewInt(1), []byte{branch})
	receipt := &types.Receipt{Status: types.ReceiptStatusSuccessful, CumulativeGasUsed: 21000, GasUsed: 21000, TxHash: tx.Hash(), BlockNumber: new(big.Int).SetUint64(number), Logs: []*types.Log{}}
	block := types.NewBlock(header, []*types.Transaction{tx}, nil, types.Receipts{receipt}, trie.NewStackTrie(nil))
	receipt.BlockHash = block.Hash()
	raw, err := rlp.EncodeToBytes(block)
	if err != nil {
		t.Fatal(err)
	}
	signed, err := tx.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}
	fixture.raw[block.Hash().Hex()+":0x0"] = signed
	fixture.receipts[tx.Hash()] = receipt
	setBackfillBlock(t, fixture, BlockEvidence{RLP: raw, Receipts: types.Receipts{receipt}})
	return block
}

func measureBacklogTimeline(t *testing.T, history *History, from, through uint64, inventory map[common.Hash]common.TicketDisplay) historyCostOperation {
	t.Helper()
	var timeline TicketTimeline
	result := measureHistoryCost(t, "ticket_tail_128", func() error {
		var err error
		timeline, err = history.TicketTimeline("node-2", from, 128)
		return err
	})
	if timeline.Status != "complete_for_retained_prefix" || timeline.Through == nil || timeline.Through.Number != through || !reflect.DeepEqual(timeline.Inventory, inventory) || len(timeline.Events) != 0 {
		t.Fatal("bounded ordinary-transfer suffix changed retained wallet inventory", timeline.Status)
	}
	return result
}

func exportBacklog(t *testing.T, history *History) []byte {
	t.Helper()
	var result bytes.Buffer
	if err := history.Export(&result); err != nil {
		t.Fatal(err)
	}
	return result.Bytes()
}

func copyClosedBacklog(t *testing.T, source, destination string) closedBacklogCopy {
	t.Helper()
	result := closedBacklogCopy{}
	err := filepath.Walk(source, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		relative, err := filepath.Rel(source, path)
		if err != nil {
			return err
		}
		target := filepath.Join(destination, relative)
		if info.IsDir() {
			return os.Mkdir(target, 0700)
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("unexpected fixture file type: %s", relative)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if err := os.WriteFile(target, data, 0600); err != nil {
			return err
		}
		copied, err := os.ReadFile(target)
		if err != nil || !bytes.Equal(copied, data) {
			return fmt.Errorf("closed copy mismatch: %s", relative)
		}
		result.Files++
		result.Bytes += int64(len(data))
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return result
}
