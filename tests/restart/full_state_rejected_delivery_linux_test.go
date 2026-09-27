package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func (a *nodeRehearsalAPI) PoolMinimumPrice() *hexutil.Big {
	return (*hexutil.Big)(a.service.TxPool().GasPrice())
}

func TestFullStateRetainedPartitionRejectedRepair(t *testing.T) {
	t.Setenv("FUSION_RESTART_REJECT_MANUAL_ONCE", "1")
	t.Setenv("FUSION_RESTART_NODE_DEBUG", "trace-json")
	rehearseRetainedPartition(t, true, true)
	root := requireRetainedPartitionRoot(t)
	var result fullStateRepairResult
	readHandoverJSON(t, filepath.Join(root, "repair-result.json"), &result)
	data, err := os.ReadFile(filepath.Join(root, "repair", fmt.Sprintf("original-%d.rlp", result.CanonicalNonce)))
	requireNoError(t, err)
	var first types.Transaction
	requireNoError(t, first.UnmarshalBinary(data))
	paths, err := filepath.Glob(filepath.Join(root, "repair", "delivery-*.jsonl"))
	requireNoError(t, err)
	confirmed := 0
	firstConfirmed := false
	for _, path := range paths {
		data, err := os.ReadFile(path)
		requireNoError(t, err)
		for _, line := range bytes.Split(data, []byte{'\n'}) {
			if len(line) == 0 {
				continue
			}
			var record struct {
				Stage          string
				Transaction    common.Hash
				DirectDelivery bool
			}
			requireNoError(t, json.Unmarshal(line, &record))
			if record.Stage == "canonical-native-success" && record.DirectDelivery {
				if record.Transaction == result.SavedHash {
					t.Fatal("saved automatic intent received direct intervention")
				}
				confirmed++
				firstConfirmed = firstConfirmed || record.Transaction == first.Hash()
			}
		}
	}
	if !firstConfirmed {
		t.Fatal("the uninterrupted sequence did not exercise successful direct recipient delivery")
	}
	t.Logf("uninterrupted rejected-predecessor intervention verified: direct purchases=%d, originals=%d, automatic successors=%d", confirmed, result.OriginalsIncluded, result.Successors)
}

func rejectFirstManualBroadcast(t *testing.T, path string, nodes [2]*rehearsalNode, owners [2]common.Address, gap livePurchaseGap, tx *types.Transaction) func() {
	t.Helper()
	recipient := nodes[1-gap.index]
	head := nodes[gap.index].status(t)
	if recipient.status(t).Hash != head.Hash {
		t.Fatal("price-rejection injection requires matching current heads")
	}
	funds := readPartitionFunds(t, nodes[gap.index], owners[:], head.Number)
	for _, ticket := range funds.Tickets {
		if ticket.Owner == owners[gap.index] {
			t.Fatal("price-rejection control requires zero tickets at the origin, so it cannot mine the original locally")
		}
	}
	var price hexutil.Big
	requireNoError(t, recipient.call(t, &price, "lab_poolMinimumPrice"))
	if (*big.Int)(&price).Cmp(tx.GasTipCap()) > 0 {
		t.Fatal("original already below the recipient's normal price threshold")
	}
	saved, err := gap.saved.MarshalBinary()
	requireNoError(t, err)
	logs, err := filepath.Glob(filepath.Join(recipient.path, "process-*.log"))
	requireNoError(t, err)
	if len(logs) != 1 {
		t.Fatal("expected one fresh recipient process log")
	}
	info, err := os.Stat(logs[0])
	requireNoError(t, err)
	trace, err := os.OpenFile(filepath.Join(path, "injected-rejection.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	t.Cleanup(func() { trace.Close() })
	record := func(stage string, extra interface{}) {
		var pools [2]deliveryPoolState
		for i, node := range nodes {
			requireNoError(t, node.call(t, &pools[i], "lab_deliveryPool"))
		}
		requireNoError(t, json.NewEncoder(trace).Encode(map[string]interface{}{"Stage": stage, "ObservedUTC": time.Now().UTC(), "Transaction": tx.Hash(), "Recipient": 1 - gap.index, "Nodes": pools, "Detail": extra}))
	}
	raised := new(big.Int).Add(tx.GasTipCap(), big.NewInt(1))
	restored := false
	restore := func() {
		if !restored {
			setRehearsalMinimumPrice(t, recipient, (*big.Int)(&price))
			restored = true
		}
	}
	t.Cleanup(restore)
	record("before-price-injection", map[string]interface{}{"Normal": &price, "Raised": (*hexutil.Big)(raised)})
	setRehearsalMinimumPrice(t, recipient, raised)
	record("price-raised", (*hexutil.Big)(raised))
	return func() {
		defer restore()
		var rejection map[string]interface{}
		awaitRehearsal(t, 10*time.Second, func() bool {
			requireContinuousMiners(t, nodes[0], nodes[1])
			data, err := os.ReadFile(logs[0])
			requireNoError(t, err)
			for _, line := range bytes.Split(data[info.Size():], []byte{'\n'}) {
				var row map[string]interface{}
				if json.Unmarshal(line, &row) == nil && row["msg"] == "Discarding invalid transaction" && row["hash"] == tx.Hash().Hex() && row["err"] == "transaction underpriced" {
					rejection = row
					return true
				}
			}
			return false
		})
		record("remote-rejection-observed", rejection)
		restore()
		record("normal-price-restored", &price)
		started := time.Now()
		for time.Since(started) < 15*time.Second {
			requireContinuousMiners(t, nodes[0], nodes[1])
			origin := readPeerPurchase(t, nodes[gap.index])
			var remote deliveryPoolState
			requireNoError(t, recipient.call(t, &remote, "lab_deliveryPool"))
			if origin.Nonce != tx.Nonce() || !bytes.Equal(origin.Saved, saved) || len(origin.Pending) != 1 || origin.Pending[0].Hash() != tx.Hash() || len(remote.Pending[owners[gap.index]])+len(remote.Queued[owners[gap.index]]) != 0 {
				t.Fatal("expected the original to remain pending only at its origin after restoring normal price")
			}
			time.Sleep(500 * time.Millisecond)
		}
		record("still-stranded-after-price-restore", nil)
		t.Logf("observed real remote underprice rejection and 15 seconds of local-only pending after normal price restoration: nonce=%d hash=%s", tx.Nonce(), tx.Hash().Hex())
	}
}

func setRehearsalMinimumPrice(t *testing.T, node *rehearsalNode, price *big.Int) {
	t.Helper()
	var accepted bool
	requireNoError(t, node.call(t, &accepted, "miner_setGasPrice", (*hexutil.Big)(price)))
	var actual hexutil.Big
	requireNoError(t, node.call(t, &actual, "lab_poolMinimumPrice"))
	if !accepted || (*big.Int)(&actual).Cmp(price) != 0 {
		t.Fatal("existing minimum-price RPC did not apply the exact test setting")
	}
}
