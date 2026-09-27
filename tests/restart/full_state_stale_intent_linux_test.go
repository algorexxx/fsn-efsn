package restart

import (
	"bytes"
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateStaleIntentRecovery(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	owners := [2]common.Address{common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
	var source [2]peerPurchaseState
	readHandoverJSON(t, filepath.Join(root, "source-results", "stopped-purchases.json"), &source)
	var head, anchor *types.Block
	var stale *types.Transaction
	var staleRaw []byte
	var transfers types.Transactions
	if !t.Run("seed-explicit-stale-fixture", func(t *testing.T) {
		f, _, funding := openFullStateHandover(t, filepath.Join(root, "producer"))
		head = f.chain.CurrentBlock()
		if head.Hash() != common.HexToHash("0x1c856076d9f7d8ab6f426a50684e581f48688e5dc41bb4bc81cee0f4d0d977cc") {
			t.Fatal("expected preserved nonce-abandonment result")
		}
		anchor = f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
		state, err := f.chain.State()
		requireNoError(t, err)
		if state.GetNonce(owners[0]) != 39 || state.GetNonce(owners[1]) != 44 || state.GetNonce(f.owner) != 233429 {
			t.Fatal("copied funding nonces changed")
		}
		original := readAutomaticPurchaseRecord(t, f.db, owners[0])
		originalRaw, err := original.MarshalBinary()
		requireNoError(t, err)
		if !bytes.Equal(originalRaw, source[0].Saved) || original.Nonce() != 39 {
			t.Fatal("source intent differs")
		}
		donation := *f
		selectHandoverSuccessor(t, &donation, funding)
		stale = donation.signPurchase(t, head.Time()-2*24*3600, head.Time()+28*24*3600)
		staleRaw, err = stale.MarshalBinary()
		requireNoError(t, err)
		pool := f.newPool(t)
		requireErrorContains(t, pool.AddLocal(stale), "BuyTicket end must be greater than latest block time + 1 month")
		for i, keyNumber := range []byte{1, 3} {
			keyBytes := make([]byte, 32)
			keyBytes[31] = keyNumber
			key, err := crypto.ToECDSA(keyBytes)
			requireNoError(t, err)
			sender := crypto.PubkeyToAddress(key.PublicKey)
			nonce := []uint64{233429, 45}[i]
			value := decimal(t, []string{"1200000000000000000000", "1800000000000000000000"}[i])
			if sender != []common.Address{f.owner, owners[1]}[i] || state.GetBalance(common.SystemAssetID, sender).Cmp(new(big.Int).Add(value, big.NewInt(42000000000000))) < 0 {
				t.Fatal("funding lacks existing synthetic liquid and gas")
			}
			tx, err := types.SignTx(types.NewTransaction(nonce, owners[0], value, 21000, big.NewInt(2000000000), nil), types.LatestSigner(f.chain.Config()), key)
			requireNoError(t, err)
			requireNoError(t, pool.AddLocal(tx))
			transfers = append(transfers, tx)
		}
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "stale-fixture.json"), map[string]interface{}{
			"Head": head.Header(), "OriginalRaw": hexutil.Bytes(originalRaw), "Original": original,
			"StaleRaw": hexutil.Bytes(staleRaw), "Stale": stale, "FixtureRecordInjection": true, "HistoricalOriginalExpired": false,
		}))
		requireNoError(t, f.db.Put(append([]byte("fsn-auto-ticket-v1-"), owners[0][:]...), staleRaw))
		if f.chain.CurrentBlock().Hash() != head.Hash() || readAutomaticPurchaseRecord(t, f.db, owners[0]).Hash() != stale.Hash() {
			t.Fatal("fixture injection changed the head or failed to preserve stale bytes")
		}
	}) {
		t.Fatal("stale fixture preparation failed")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-plan.json"), map[string]interface{}{"Source": head.Header(), "Transfers": transfers, "ExistingSyntheticBalances": true}))
	history, err := os.ReadFile(filepath.Join(root, "source-results", "neutralizations.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(history, &ordinary))
	ordinary = append(ordinary, transfers...)
	writeStaleIntentAllowlist(t, root, ordinary)
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 5*time.Minute)}
	for i, node := range nodes {
		expected := source[i]
		if i == 0 {
			expected.Saved = staleRaw
		}
		requirePausedPurchaseState(t, node, head, expected)
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("stale fixture requires empty initial pools")
		}
	}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	startCompetingMiner(t, nodes[0])
	recordStaleIntentWindow(t, root, "unfunded", nodes, staleRaw)
	startCompetingMiner(t, nodes[1])
	donor := awaitFullStateFundingDonor(t, nodes, 1)
	if donor.Nonce != 44 {
		t.Fatal("funding donor advanced before its reviewed nonce-45 transfer could be staged")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "donor-before-funding.json"), donor))
	var hash common.Hash
	for _, tx := range transfers {
		raw, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, nodes[1].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw)))
		if hash != tx.Hash() {
			t.Fatal("funding submission changed identity")
		}
	}
	var fundingReceipts types.Receipts
	for _, tx := range transfers {
		fundingReceipts = append(fundingReceipts, awaitLiveFundingTransfer(t, nodes, tx))
	}
	recordStaleIntentWindow(t, root, "funded", nodes, staleRaw)
	before := nodes[0].status(t)
	backup := common.HexToAddress("0x7e5f4552091a69125d5dfcb7b8c2659029395bdf")
	funds := readPartitionFunds(t, nodes[0], append([]common.Address{backup}, owners[:]...), before.Number)
	if funds.Accounts[owners[0]].BalancesVal[0].String() != "5021976763487999978776" {
		t.Fatal("stale intent did not remain blocked after exact 3000 FSN funding")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funded-stale-state.json"), map[string]interface{}{"Header": funds.Block.Header(), "Accounts": funds.Accounts, "Tickets": funds.Tickets, "Receipts": fundingReceipts}))
	cancel := signNeutralizationRPC(t, nodes[0], owners[0], owners[0], 39, 21000, nil)
	ordinary = append(ordinary, cancel)
	writeStaleIntentAllowlist(t, root, ordinary)
	raw, err := cancel.MarshalBinary()
	requireNoError(t, err)
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "abandonment.json"), map[string]interface{}{"Before": funds.Block.Header(), "Transaction": cancel, "Raw": hexutil.Bytes(raw)}))
	requireNoError(t, nodes[1].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw)))
	if hash != cancel.Hash() {
		t.Fatal("abandonment submission changed identity")
	}
	abandoned := awaitLiveFundingTransfer(t, nodes, cancel)
	trace, err := os.OpenFile(filepath.Join(root, "progress.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	observe := func() {
		row := equalWeightObservation{Phase: "automatic-recovery", ObservedUTC: time.Now().UTC()}
		for i, node := range nodes {
			row.Nodes[i], row.Purchases[i] = node.status(t), readPeerPurchase(t, node)
		}
		requireNoError(t, json.NewEncoder(trace).Encode(row))
	}
	live := awaitContinuousMinerProgressObserved(t, nodes[0], nodes[1], owners, [2]uint64{42, 47}, abandoned.BlockNumber.Uint64(), 300*time.Second, observe)
	var recovered types.Transactions
	produced := false
	for number := abandoned.BlockNumber.Uint64() + 1; number <= live.NumberU64(); number++ {
		block := readRecoveryNodeBlock(t, nodes[0], number)
		produced = produced || block.Coinbase() == owners[0]
		for _, tx := range block.Transactions() {
			sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			if sender == owners[0] {
				if !tx.IsBuyTicketTx() || tx.Nonce() != uint64(40+len(recovered)) || readCanonicalRepairReceipt(t, nodes, tx, owners[0]) == nil {
					t.Fatal("fresh purchases did not execute in sequence with canonical native success")
				}
				recovered = append(recovered, tx)
			}
		}
	}
	if !produced || len(recovered) < 3 {
		t.Fatal("recovered owner must buy at least three fresh tickets and sign a canonical block")
	}
	for _, node := range nodes {
		var receipt *types.Receipt
		requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", stale.Hash()))
		if receipt != nil {
			t.Fatal("abandoned stale purchase acquired a canonical receipt")
		}
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		if bytes.Equal(stopped[i].Saved, staleRaw) {
			t.Fatal("consumed stale intent remains saved")
		}
		node.stop(t, false)
	}
	requirePurchaseLogContains(t, paths[0], "BuyTicket end must be greater than latest block time + 1 month")
	requirePurchaseLogContains(t, paths[0], "Automatic ticket nonce consumed without a confirmed purchase")
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stale-recovery-result.json"), map[string]interface{}{
		"Before": head.Header(), "Live": live.Header(), "Final": final.Header(), "Stale": stale,
		"AbandonmentReceipt": abandoned, "FreshPurchases": recovered, "DonationProduced": produced,
		"FixtureRecordInjection": true, "RecoveryRecordEdits": false, "FundingWei": "3000000000000000000000",
	}))
	t.Logf("stale nonce 39 stayed unchanged before/after funding; explicit self-transfer retired it without false confirmation; %d fresh donation purchases and canonical mining resumed; final=%d %s", len(recovered), final.NumberU64(), final.Hash().Hex())
}

func writeStaleIntentAllowlist(t *testing.T, root string, transactions types.Transactions) {
	t.Helper()
	raw, err := rlp.EncodeToBytes(transactions)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(root, "ordinary-transactions.rlp"), raw, 0600))
}

func recordStaleIntentWindow(t *testing.T, root, phase string, nodes [2]*rehearsalNode, raw []byte) {
	t.Helper()
	var rows []map[string]interface{}
	start := time.Now()
	for time.Since(start) < 12*time.Second {
		purchase := readPeerPurchase(t, nodes[0])
		status := nodes[0].status(t)
		if purchase.Nonce != 39 || !bytes.Equal(purchase.Saved, raw) || len(purchase.Pending)+len(purchase.Queued) != 0 || !status.Mining || !status.AutoBuy {
			t.Fatal("enabled buyer changed stale bytes, nonce or own pool before explicit abandonment")
		}
		var errors [2]string
		for i, node := range nodes {
			var hash common.Hash
			err := node.call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw))
			requireErrorContains(t, err, "BuyTicket end must be greater than latest block time + 1 month")
			errors[i] = err.Error()
		}
		rows = append(rows, map[string]interface{}{"ObservedUTC": time.Now().UTC(), "Purchase": purchase, "Node": status, "Errors": errors})
		time.Sleep(time.Second)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, phase+"-stale.json"), rows))
}

func TestFullStateStaleIntentColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	raw, err := os.ReadFile(filepath.Join(root, "ordinary-transactions.rlp"))
	requireNoError(t, err)
	var ordinary types.Transactions
	requireNoError(t, rlp.DecodeBytes(raw, &ordinary))
	if len(ordinary) != 33 && len(ordinary) != 34 {
		t.Fatal("expected prior 31 self-transfers, two funding transfers and optional abandonment")
	}
	auditRetainedPartitionCold(t, root, ordinary)
}
