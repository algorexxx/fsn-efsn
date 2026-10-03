package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

func requireServiceAnchorInventory(t *testing.T, binary, output, history string, nodes [2]*rehearsalNode, ipc, http observe.Config, anchor observerServiceTruth, truth [2]observerServiceTruth) {
	t.Helper()
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "anchor-inventory-truth.json"), anchor))
	for i, configName := range []string{"ipc-divergence", "http-divergence"} {
		node := ipc.Nodes[i].Name
		var missing observe.TicketTimeline
		requireNoError(t, json.Unmarshal(runServiceHistory(t, binary, output, node+"-before-anchor", nodes, "--history", history, "--ticket-timeline", node, "--ticket-blocks", "128"), &missing))
		if missing.Status != "missing_baseline" || nodes[i].status(t).Number <= ipc.AnchorNumber {
			t.Fatal("historical acquisition did not start after the anchor with a missing baseline")
		}
		var inventory observe.AnchorInventory
		raw := runServiceHistory(t, binary, output, node+"-anchor-inventory", nodes, "--config", filepath.Join(output, configName+"-config.json"), "--history", history, "--timeout", "5s", "--anchor-inventory", node)
		requireNoError(t, json.Unmarshal(raw, &inventory))
		if inventory.Status != "ready" || inventory.Anchor == nil || inventory.AnchorAfter == nil || inventory.Anchor.Hash != ipc.AnchorHash || inventory.AnchorAfter.Hash != ipc.AnchorHash || !bytes.Equal(mustObserverJSON(t, inventory.Tickets), mustObserverJSON(t, anchor.Tickets)) {
			t.Fatal("historical RPC inventory differs from independently saved anchor state", inventory.Status)
		}
		requireServiceTicketTimeline(t, binary, output, node+"-anchor-timeline", history, nodes, node, truth[i])
	}
	empty := http
	empty.Nodes = append([]observe.NodeConfig(nil), http.Nodes...)
	empty.Nodes[1].Wallet = common.HexToAddress("0x0000000000000000000000000000000000000099")
	path := filepath.Join(output, "empty-wallet-config.json")
	requireNoError(t, writeStateExportJSON(path, empty))
	emptyHistory := filepath.Join(t.TempDir(), "empty-wallet-history")
	runServiceHistory(t, binary, output, "empty-wallet-init", nodes, "--config", path, "--history", emptyHistory, "--init-history", "--history-budget", "1048576")
	var response json.RawMessage
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	batch := []rpc.BatchElem{{Method: "fsn_allTicketsByAddress", Args: []interface{}{empty.Nodes[1].Wallet, hexutil.EncodeUint64(empty.AnchorNumber)}, Result: &response}}
	requireNoError(t, nodes[1].client.BatchCallContext(ctx, batch))
	requireNoError(t, batch[0].Error)
	if string(response) != "null" {
		t.Fatal("expected the inherited empty-owner RPC null result", string(response))
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(output, "empty-wallet-native-response.json"), response))
	var inventory observe.AnchorInventory
	requireNoError(t, json.Unmarshal(runServiceHistory(t, binary, output, "empty-wallet-anchor", nodes, "--config", path, "--history", emptyHistory, "--timeout", "5s", "--anchor-inventory", "node-2"), &inventory))
	if inventory.Status != "ready" || inventory.Tickets == nil || len(inventory.Tickets) != 0 {
		t.Fatal("empty historical wallet is not an explicit empty inventory")
	}
}

func requireServiceTicketTimeline(t *testing.T, binary, output, name, history string, nodes [2]*rehearsalNode, node string, truth observerServiceTruth) {
	t.Helper()
	var timeline observe.TicketTimeline
	raw := runServiceHistory(t, binary, output, name, nodes, "--history", history, "--ticket-timeline", node, "--ticket-blocks", "128")
	requireNoError(t, json.Unmarshal(raw, &timeline))
	if timeline.Status != "complete_for_retained_prefix" || timeline.Through == nil || timeline.Through.Hash != truth.Header.Hash() || !bytes.Equal(mustObserverJSON(t, timeline.Inventory), mustObserverJSON(t, truth.Tickets)) {
		t.Fatal("historical baseline did not reconstruct the independent current state", timeline.Status)
	}
}
