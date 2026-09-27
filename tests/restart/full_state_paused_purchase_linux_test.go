package restart

import (
	"bytes"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStatePausedPurchaseDiagnosis(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	var source struct {
		Stopped     equalWeightObservation
		BeforePause equalWeightObservation
	}
	readHandoverJSON(t, filepath.Join(root, "source-results", "pause-result.json"), &source)
	owners := [2]common.Address{common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
	originals := make(map[uint64]*types.Transaction)
	locations := make(map[uint64]*types.Block)
	var head, anchor *types.Block
	var saved [2]*types.Transaction
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			head = f.chain.CurrentBlock()
			if head.Hash() != common.HexToHash("0x0e01aeb3c7e60ad34d818e6fe784af1aaf72e09602975815dcac263a4feaea91") || head.Hash() != source.Stopped.Nodes[i].Hash || head.Root() != source.Stopped.Nodes[i].Root || head.MixDigest() != source.Stopped.Nodes[i].Tickets {
				t.Fatal("expected the retained coordinated-pause result")
			}
			candidate := f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			if candidate == nil || (anchor != nil && candidate.Hash() != anchor.Hash()) {
				t.Fatal("missing shared recovery anchor")
			}
			anchor = candidate
			state, err := f.chain.State()
			requireNoError(t, err)
			data, err := f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...))
			requireNoError(t, err)
			saved[i] = new(types.Transaction)
			requireNoError(t, saved[i].UnmarshalBinary(data))
			sender, err := types.Sender(types.LatestSigner(f.chain.Config()), saved[i])
			requireNoError(t, err)
			if sender != owners[i] || !saved[i].IsBuyTicketTx() || saved[i].Nonce() != [2]uint64{39, 40}[i] || state.GetNonce(sender) != [2]uint64{8, 40}[i] || !bytes.Equal(data, source.Stopped.Purchases[i].Saved) {
				t.Fatal("retained canonical nonce, signed intent or owner changed")
			}
			if i == 0 {
				for number := anchor.NumberU64() + 1; number <= source.BeforePause.Nodes[0].Number; number++ {
					for _, hash := range rawdb.ReadAllHashes(f.db, number) {
						if hash == rawdb.ReadCanonicalHash(f.db, number) {
							continue
						}
						block := f.chain.GetBlock(hash, number)
						if block == nil {
							t.Fatal("noncanonical header has no stored body")
						}
						for _, tx := range block.Transactions() {
							retainLivePurchase(t, owners[0], originals, tx)
							if originals[tx.Nonce()] != nil && originals[tx.Nonce()].Hash() == tx.Hash() {
								locations[tx.Nonce()] = block
							}
						}
					}
				}
			}
		}) {
			t.Fatal("paused-purchase preflight failed")
		}
	}
	encoded, err := os.ReadFile(filepath.Join(root, "source-results", "isolated-producer.rlp"))
	requireNoError(t, err)
	var branch types.Blocks
	requireNoError(t, rlp.DecodeBytes(encoded, &branch))
	for nonce := uint64(8); nonce < 39; nonce++ {
		if originals[nonce] == nil || locations[nonce] == nil {
			t.Fatalf("missing original nonce %d in local displaced bodies", nonce)
		}
		found := false
		for _, block := range branch {
			for _, tx := range block.Transactions() {
				found = found || (block.Hash() == locations[nonce].Hash() && tx.Hash() == originals[nonce].Hash())
			}
		}
		if !found {
			t.Fatal("discovered original differs from independently retained pre-pause branch")
		}
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 3*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 3*time.Minute)}
	for i, node := range nodes {
		requirePausedPurchaseState(t, node, head, source.Stopped.Purchases[i])
		status := node.status(t)
		if status.Pending+status.Queued != 0 {
			t.Fatal("diagnosis requires empty startup pools")
		}
	}
	recovered := filepath.Join(root, "recovered")
	requireNoError(t, os.Mkdir(recovered, 0700))
	funds := readPartitionFunds(t, nodes[0], append([]common.Address{common.HexToAddress("0x7e5f4552091a69125d5dfcb7b8c2659029395bdf")}, owners[:]...), head.NumberU64())
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funds.json"), funds))
	var records []map[string]interface{}
	for nonce := uint64(8); nonce <= 39; nonce++ {
		tx := saved[0]
		var oldHash common.Hash
		var oldNumber uint64
		if nonce < 39 {
			tx = requireDisplacedPurchaseRPC(t, nodes[0], locations[nonce], originals[nonce])
			oldHash, oldNumber = locations[nonce].Hash(), locations[nonce].NumberU64()
		}
		data, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(recovered, fmt.Sprintf("purchase-%d.rlp", nonce)), data, 0600))
		row := diagnosePausedPurchaseAdmission(t, nodes, head, owners[0], tx, funds)
		row["OriginalBlock"], row["OriginalHeight"] = oldHash, oldNumber
		records = append(records, row)
	}
	for i, node := range nodes {
		var returned common.Hash
		data, err := saved[1].MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, node.call(t, &returned, "eth_sendRawTransaction", hexutil.Bytes(data)))
		if returned != saved[1].Hash() {
			t.Fatal("positive control changed the entrant purchase")
		}
		awaitRehearsal(t, 5*time.Second, func() bool { return node.status(t).Pending == 1 && node.status(t).Queued == 0 })
		requirePausedPurchaseState(t, node, head, source.Stopped.Purchases[i])
	}
	nodes[0].stop(t, false)
	nodes[0] = startRehearsalNodeWithTimeout(t, paths[0], 3*time.Minute)
	for nonce := uint64(8); nonce < 39; nonce++ {
		requireDisplacedPurchaseRPC(t, nodes[0], locations[nonce], originals[nonce])
	}
	var stopped [2]peerPurchaseState
	var statuses [2]nodeRehearsalStatus
	for i, node := range nodes {
		requirePausedPurchaseState(t, node, head, source.Stopped.Purchases[i])
		stopped[i], statuses[i] = readPeerPurchase(t, node), node.status(t)
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "paused-purchase-result.json"), map[string]interface{}{
		"Head": head.Header(), "Owner": owners[0], "Records": records, "RetrievedBeforeAndAfterRestart": 31,
		"PositiveControl": saved[1], "PositiveControlAcceptedBoth": true, "Stopped": statuses,
		"CanonicalStateUnchanged": true, "SavedIntentsUnchanged": true, "NewFunding": false, "MiningEnabled": false,
	}))
	t.Log("31 displaced originals retrieved exactly before and after restart; all 32 donation purchases fail funding on both nodes while the entrant control is admitted; no canonical state or saved intent changed")
}

func requirePausedPurchaseState(t *testing.T, node *rehearsalNode, head *types.Block, expected peerPurchaseState) {
	t.Helper()
	status := node.status(t)
	requireRehearsalHead(t, status, head)
	purchase := readPeerPurchase(t, node)
	if status.Mining || status.AutoBuy || purchase.Nonce != expected.Nonce || !bytes.Equal(purchase.Saved, expected.Saved) {
		t.Fatal("paused diagnostic changed worker state, canonical nonce or saved intent")
	}
}

func diagnosePausedPurchaseAdmission(t *testing.T, nodes [2]*rehearsalNode, head *types.Block, owner common.Address, tx *types.Transaction, funds partitionFunds) map[string]interface{} {
	t.Helper()
	var call common.FSNCallParam
	requireNoError(t, rlp.DecodeBytes(tx.Data(), &call))
	var purchase common.BuyTicketParam
	requireNoError(t, rlp.DecodeBytes(call.Data, &purchase))
	sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
	requireNoError(t, err)
	if sender != owner || call.Func != common.BuyTicketFunc || tx.GasPrice().Cmp(head.BaseFee()) < 0 {
		t.Fatal("original owner, native type or fee is invalid")
	}
	requireNoError(t, purchase.Check(common.BigMaxUint64, head.Time()))
	deadline := purchase.End - 29*24*3600
	requireNoError(t, purchase.Check(common.BigMaxUint64, deadline))
	requireErrorContains(t, purchase.Check(common.BigMaxUint64, deadline+1), "latest block time")
	observed := time.Now().UTC()
	start := common.MaxUint64(purchase.Start, uint64(observed.Unix()))
	account := funds.Accounts[owner]
	coverage := account.TimeLockBalancesVal[0].GetSpendableValue(start, purchase.End)
	price := common.TicketPrice(head.Number())
	if coverage.Sign() != 0 || account.BalancesVal[0].Cmp(price) >= 0 {
		t.Fatal("expected zero free interval coverage and less than one ticket of liquid funds")
	}
	need := new(big.Int).Mul(new(big.Int).SetUint64(tx.Gas()), tx.GasPrice())
	need.Add(need, common.GetFsnCallFee(tx.To(), call.Func))
	need.Add(need, price)
	data, err := tx.MarshalBinary()
	requireNoError(t, err)
	var errors [2]string
	for i, node := range nodes {
		var returned common.Hash
		err := node.call(t, &returned, "eth_sendRawTransaction", hexutil.Bytes(data))
		requireErrorContains(t, err, "insufficient balance")
		errors[i] = err.Error()
		requireRehearsalHead(t, node.status(t), head)
	}
	return map[string]interface{}{"Transaction": tx, "Nonce": tx.Nonce(), "Hash": tx.Hash(), "ObservedUTC": observed,
		"Purchase": purchase, "FundingStart": start, "FreeCoverageWei": coverage.String(), "LiquidWei": account.BalancesVal[0].String(),
		"LiquidRequiredWei": need.String(), "AdditionalLiquidWei": new(big.Int).Sub(need, account.BalancesVal[0]).String(),
		"LatestPoolHeadTimestamp": deadline, "RemainingHeadSeconds": deadline - head.Time(), "DeadlineBoundaryChecked": true, "PoolErrors": errors}
}
