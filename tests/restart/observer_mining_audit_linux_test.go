package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func auditObserverMiningHistory(t *testing.T, output string, initial, exported []byte, config observe.Config, nodes [2]*rehearsalNode, producer int, final *types.Block) map[string]int {
	t.Helper()
	var anchorReport observe.Report
	requireNoError(t, json.Unmarshal(initial, &anchorReport))
	tickets := make(map[common.Hash]common.TicketDisplay)
	for i, node := range anchorReport.Nodes {
		if node.Head.Hash != config.AnchorHash || !node.TicketsKnown || node.Identity != "matches" || node.Consistency != "stable" || node.Wallet != config.Nodes[i].Wallet {
			t.Fatal("missing complete two-owner anchor inventory")
		}
		for id, ticket := range node.Tickets {
			if ticket.Owner != node.Wallet || ticket.Height == 0 {
				t.Fatal("expected known non-genesis owner tickets at anchor")
			}
			tickets[id] = ticket
		}
	}
	blocks := make(map[string]map[uint64]observe.BlockEvidence)
	for _, node := range config.Nodes {
		blocks[node.Name] = make(map[uint64]observe.BlockEvidence)
	}
	decoder := json.NewDecoder(bytes.NewReader(exported))
	for {
		var event struct{ Backfill *observe.BackfillReport }
		err := decoder.Decode(&event)
		if err == io.EOF {
			break
		}
		requireNoError(t, err)
		if event.Backfill == nil {
			continue
		}
		for _, evidence := range event.Backfill.Blocks {
			var block types.Block
			requireNoError(t, rlp.DecodeBytes(evidence.RLP, &block))
			if _, exists := blocks[event.Backfill.Node][block.NumberU64()]; exists {
				t.Fatal("unforked live history fetched the same block twice")
			}
			blocks[event.Backfill.Node][block.NumberU64()] = evidence
		}
	}
	counts := map[string]int{"anchor_tickets": len(tickets), "blocks": 0, "purchases": 0, "selections": 0, "retreats": 0, "expired": 0}
	var events []map[string]interface{}
	parent := anchorReport.Nodes[0].Head.Header
	owners := []common.Address{config.Nodes[0].Wallet, config.Nodes[1].Wallet}
	for height := config.AnchorNumber + 1; height <= final.NumberU64(); height++ {
		left, leftOK := blocks[config.Nodes[0].Name][height]
		right, rightOK := blocks[config.Nodes[1].Name][height]
		if !leftOK || !rightOK || !bytes.Equal(mustObserverJSON(t, left), mustObserverJSON(t, right)) {
			t.Fatalf("observer history incomplete or inconsistent at %d", height)
		}
		var block types.Block
		requireNoError(t, rlp.DecodeBytes(left.RLP, &block))
		if block.ParentHash() != parent.Hash() || block.Coinbase() != config.Nodes[producer].Wallet {
			t.Fatal("retained evidence is not the single producer's contiguous branch")
		}
		for _, node := range nodes {
			canonical := readRecoveryNodeBlock(t, node, height)
			encoded, err := rlp.EncodeToBytes(canonical)
			requireNoError(t, err)
			if !bytes.Equal(encoded, left.RLP) {
				t.Fatal("retained raw block differs from node history")
			}
			for i, tx := range block.Transactions() {
				var receipt *types.Receipt
				requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
				if !bytes.Equal(mustObserverJSON(t, receipt), mustObserverJSON(t, left.Receipts[i])) {
					t.Fatal("retained receipt differs from node history")
				}
			}
		}
		for i, tx := range block.Transactions() {
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			if !tx.IsBuyTicketTx() || owner != config.Nodes[producer].Wallet {
				t.Fatal("unexpected transaction in automatic-buy-only fixture")
			}
			requirePeerNativePurchase(t, left.Receipts[i], &block, tx, owner)
			var envelope common.FSNCallParam
			var interval common.BuyTicketParam
			requireNoError(t, rlp.DecodeBytes(tx.Data(), &envelope))
			requireNoError(t, rlp.DecodeBytes(envelope.Data, &interval))
			parentHash := block.ParentHash()
			id := crypto.Keccak256Hash(owner[:], parentHash[:])
			if _, exists := tickets[id]; exists {
				t.Fatal("duplicate ticket purchase ID")
			}
			ticket := common.TicketDisplay{Owner: owner, Height: height, StartTime: interval.Start, ExpireTime: interval.End, Value: common.TicketPrice(block.Number())}
			tickets[id] = ticket
			events = append(events, map[string]interface{}{"Kind": "purchase", "Block": block.Hash(), "Height": height, "TicketID": id, "Ticket": ticket, "Transaction": tx.Hash()})
			counts["purchases"]++
		}
		if len(block.Extra()) < 32+5+65 {
			t.Fatal("snapshot data shorter than count/checksum framing")
		}
		snapshot, err := datong.NewSnapshotFromHeader(block.Header())
		requireNoError(t, err)
		for i, id := range append([]common.Hash{snapshot.Selected}, snapshot.Retreat...) {
			ticket, exists := tickets[id]
			if !exists || ticket.Height >= height || i == 0 && ticket.Owner != block.Coinbase() {
				t.Fatal("selection/retreat lacks parent ticket ownership")
			}
			kind := "selection"
			counts["selections"]++
			if i > 0 {
				kind = "retreat"
				counts["selections"]--
				counts["retreats"]++
			}
			events = append(events, map[string]interface{}{"Kind": kind, "Block": block.Hash(), "Height": height, "TicketID": id, "Ticket": ticket, "RetreatIndex": i - 1, "ReturnExpected": i != 1 && ticket.ExpireTime > block.Time()})
			delete(tickets, id)
		}
		for id, ticket := range tickets {
			if ticket.ExpireTime <= parent.Time {
				events = append(events, map[string]interface{}{"Kind": "expiry", "Block": block.Hash(), "Height": height, "TicketID": id, "Ticket": ticket})
				delete(tickets, id)
				counts["expired"]++
			}
		}
		actual := readPartitionFunds(t, nodes[0], owners, height)
		other := readPartitionFunds(t, nodes[1], owners, height)
		if len(tickets) != snapshot.TicketNumber || !bytes.Equal(mustObserverJSON(t, tickets), mustObserverJSON(t, actual.Tickets)) || !bytes.Equal(mustObserverJSON(t, actual.Tickets), mustObserverJSON(t, other.Tickets)) {
			t.Fatal("reconstructed owner inventory differs from executed state or header count")
		}
		requireNoError(t, os.WriteFile(filepath.Join(output, fmt.Sprintf("block-%d.rlp", height)), left.RLP, 0600))
		requireNoError(t, writeStateExportJSON(filepath.Join(output, fmt.Sprintf("ledger-%d.json", height)), map[string]interface{}{"Header": block.Header(), "Receipts": left.Receipts, "Tickets": actual.Tickets, "Accounts": actual.Accounts}))
		counts["blocks"]++
		parent = block.Header()
	}
	if parent.Hash() != final.Hash() || counts["purchases"] < 3 || counts["retreats"] == 0 {
		t.Fatal("expected actual purchases, selection and fallback retreat evidence", counts)
	}
	counts["final_tickets"] = len(tickets)
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "native-events.json"), events))
	return counts
}
