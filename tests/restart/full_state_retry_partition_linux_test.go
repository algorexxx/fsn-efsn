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
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func requireRetainedPartitionRoot(t *testing.T) string {
	t.Helper()
	root := os.Getenv("FUSION_RESTART_RETRY_PARTITION")
	if root == "" {
		t.Skip("requires fresh retained-participant copies")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and isolated rehearsal required")
	}
	return root
}

func TestFullStateRetainedPartitionRepair(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	var cleanup, retained fullStateBlockLedger
	readHandoverJSON(t, filepath.Join(root, "retained-blocks", "block-03.json"), &cleanup)
	readHandoverJSON(t, filepath.Join(root, "retained-blocks", "block-10.json"), &retained)
	if retained.Header.Hash() != common.HexToHash("0x71fda3d5913b4f0ae5ea48fb1512bf3f1706a2b42a4d9358b1cd890f95ff8674") {
		t.Fatal("expected the preserved funded participant checkpoint")
	}
	for _, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			if f.chain.CurrentBlock().Hash() != retained.Header.Hash() {
				t.Fatal("retained checkpoint differs")
			}
			owners := []common.Address{f.owner, common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
			var saved [2]*types.Transaction
			state, err := f.chain.State()
			requireNoError(t, err)
			pool := f.newPool(t)
			for i, owner := range owners[1:] {
				key := append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
				exists, err := f.db.Has(key)
				requireNoError(t, err)
				if !exists {
					continue
				}
				data, err := f.db.Get(key)
				requireNoError(t, err)
				saved[i] = new(types.Transaction)
				requireNoError(t, saved[i].UnmarshalBinary(data))
				sender, err := types.Sender(types.LatestSigner(f.chain.Config()), saved[i])
				requireNoError(t, err)
				if sender != owner || !saved[i].IsBuyTicketTx() || saved[i].Nonce() > state.GetNonce(owner) {
					t.Fatal("retained intent has wrong owner, payload or nonce gap")
				}
				if saved[i].Nonce() == state.GetNonce(owner) {
					requireNoError(t, pool.AddLocal(saved[i]))
				}
			}
			recordFundingInventory(t, root, "preflight-"+role, f, owners, saved)
		}) {
			t.Fatal("retained checkpoint preflight failed")
		}
	}
	installFullStateHistory(t, root)
	rehearseFullStatePartitionRepair(t, root, types.NewBlockWithHeader(cleanup.Header), types.NewBlockWithHeader(retained.Header))
}

func requireFullStatePartitionReserve(t *testing.T, root string, nodes [2]*rehearsalNode, owners [2]common.Address, head *types.Block) {
	t.Helper()
	funds := readPartitionFunds(t, nodes[0], owners[:], head.NumberU64())
	if funds.Block.Hash() != head.Hash() || readRecoveryNodeBlock(t, nodes[1], head.NumberU64()).Hash() != head.Hash() {
		t.Fatal("reserve checkpoint changed")
	}
	start := common.MaxUint64(head.Time(), uint64(time.Now().Unix()))
	end := start + 30*24*3600
	price := decimal(t, "5000000000000000000000")
	gas := decimal(t, "200000000000000")
	var records []map[string]interface{}
	ready := true
	for i, owner := range owners {
		purchase := readPeerPurchase(t, nodes[i])
		eligible := 0
		account := funds.Accounts[owner]
		returned := new(common.TimeLock).Set(account.TimeLockBalancesVal[0])
		for _, ticket := range funds.Tickets {
			if ticket.Owner == owner && ticket.Height <= head.NumberU64() && ticket.StartTime <= head.Time() && ticket.ExpireTime >= ticket.StartTime+30*24*3600 && ticket.ExpireTime > start+15*60 {
				eligible++
				returned.Add(returned, common.NewTimeLock(&common.TimeLockItem{StartTime: start, EndTime: ticket.ExpireTime, Value: ticket.Value}))
			}
		}
		coverage := account.TimeLockBalancesVal[0].GetSpendableValue(start, end)
		liquid := account.BalancesVal[0]
		funded := liquid.Cmp(new(big.Int).Add(price, gas)) >= 0 || (coverage.Cmp(price) >= 0 && liquid.Cmp(gas) >= 0)
		backing := new(big.Int).Add(returned.GetSpendableValue(start, end), liquid)
		committed := eligible >= 2 && liquid.Cmp(gas) >= 0 && backing.Cmp(new(big.Int).Add(new(big.Int).Mul(price, big.NewInt(2)), gas)) >= 0
		gap := false
		var saved types.Transaction
		if len(purchase.Saved) > 0 {
			requireNoError(t, saved.UnmarshalBinary(purchase.Saved))
			if saved.Nonce() > purchase.Nonce {
				gap = true
			}
		}
		records = append(records, map[string]interface{}{"Owner": owner, "EligibleTickets": eligible, "LiquidWei": liquid.String(), "TimeLocks": account.TimeLockBalancesVal[0], "CoverageWei": coverage.String(), "WindowStart": start, "WindowEnd": end, "GasBudgetWei": gas.String(), "FundedNextPurchase": funded, "BackingAfterNormalSelectionWei": backing.String(), "TwoCommittedTickets": committed, "NonceGap": gap, "Purchase": purchase})
		ready = ready && eligible > 0 && !gap && (funded || committed)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "before-outage.json"), map[string]interface{}{"Header": head.Header(), "Owners": records, "Ready": ready, "NewFunding": false}))
	if !ready {
		t.Fatal("outage not injected: both owners need an eligible ticket plus either a funded purchase or a second ticket backed across the interval, with no saved nonce gap")
	}
	t.Logf("both producers have an eligible ticket plus spendable or already committed second-ticket backing at %d; normal-selection backing is not a guarantee against retreat losses; no new funding", head.NumberU64())
}

func TestFullStateRetainedPartitionColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	auditRetainedPartitionCold(t, root, nil)
}

func auditRetainedPartitionCold(t *testing.T, root string, transfers types.Transactions) {
	t.Helper()
	var heads [2]*types.Header
	var funding [2]map[common.Hash]uint64
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run(role, func(t *testing.T) {
			f, _, fixtureFunding := openFullStateHandover(t, filepath.Join(root, role))
			head := f.chain.CurrentBlock()
			heads[i] = head.Header()
			base := fixtureFunding.Parent.Number.Uint64()
			funding[i] = make(map[common.Hash]uint64)
			artifacts := filepath.Join(root, "audit-"+role)
			requireNoError(t, os.Mkdir(artifacts, 0700))
			for height := base + 1; height <= head.NumberU64(); height++ {
				block := f.chain.GetBlockByNumber(height)
				recordFullStateHandoverBlock(t, f, artifacts, base, block)
				for _, tx := range block.Transactions() {
					for _, transfer := range transfers {
						if tx.Hash() == transfer.Hash() {
							funding[i][tx.Hash()] = height
						}
					}
				}
			}
			auditFullStateHandover(t, filepath.Join(root, role), artifacts, 3)
			auditFullStateParticipantTransfers(t, artifacts, int(head.NumberU64()-base), funding[i])
			owners := []common.Address{f.owner, common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
			var saved [2]*types.Transaction
			var intents []map[string]interface{}
			state, err := f.chain.State()
			requireNoError(t, err)
			for j, owner := range owners[1:] {
				key := append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
				exists, err := f.db.Has(key)
				requireNoError(t, err)
				var data []byte
				if exists {
					data, err = f.db.Get(key)
					requireNoError(t, err)
					saved[j] = new(types.Transaction)
					requireNoError(t, saved[j].UnmarshalBinary(data))
				}
				intents = append(intents, map[string]interface{}{"Owner": owner, "Nonce": state.GetNonce(owner), "Saved": hexutil.Bytes(data), "Transaction": saved[j]})
			}
			requireNoError(t, writeStateExportJSON(filepath.Join(root, "cold-intents-"+role+".json"), intents))
			recordFundingInventory(t, root, "cold-"+role, f, owners, saved)
			encoded, err := os.ReadFile(filepath.Join(root, "isolated-"+role+".rlp"))
			if os.IsNotExist(err) {
				return
			}
			requireNoError(t, err)
			var branch types.Blocks
			requireNoError(t, rlp.DecodeBytes(encoded, &branch))
			isolated := filepath.Join(root, "audit-isolated-"+role)
			requireNoError(t, os.Mkdir(isolated, 0700))
			for _, block := range branch {
				recordFullStateHandoverBlock(t, f, isolated, base, block)
			}
			auditFullStateHandover(t, filepath.Join(root, role), isolated, 3)
			auditFullStateParticipant(t, isolated, len(branch))
		}) {
			t.Fatal("cold full-state partition audit failed")
		}
	}
	matched := heads[0].Hash() == heads[1].Hash()
	if matched {
		for i := 1; i <= int(heads[0].Number.Uint64()-15130080); i++ {
			for _, extension := range []string{"json", "rlp"} {
				name := fmt.Sprintf("block-%02d.%s", i, extension)
				left, err := os.ReadFile(filepath.Join(root, "audit-producer", name))
				requireNoError(t, err)
				right, err := os.ReadFile(filepath.Join(root, "audit-verifier", name))
				requireNoError(t, err)
				if !bytes.Equal(left, right) {
					t.Fatal("common cold canonical artifacts differ")
				}
			}
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "cold-audit.json"), map[string]interface{}{"Heads": heads, "CommonHead": matched, "LedgerPassed": true, "AdditionalFunding": funding}))
}
