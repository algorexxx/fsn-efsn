package restart

import (
	"bytes"
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

func TestFullStateExplicitNonceNeutralization(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	var source struct{ Stopped equalWeightObservation }
	readHandoverJSON(t, filepath.Join(root, "source-results", "pause-result.json"), &source)
	owner := common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf")
	var head, anchor *types.Block
	if !t.Run("preflight", func(t *testing.T) {
		f, _, funding := openFullStateHandover(t, filepath.Join(root, "producer"))
		head = f.chain.CurrentBlock()
		if head.Hash() != common.HexToHash("0x0e01aeb3c7e60ad34d818e6fe784af1aaf72e09602975815dcac263a4feaea91") {
			t.Fatal("expected preserved pause result")
		}
		anchor = f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
	}) {
		t.Fatal("preflight failed")
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 5*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 5*time.Minute)}
	for i, node := range nodes {
		requirePausedPurchaseState(t, node, head, source.Stopped.Purchases[i])
		if status := node.status(t); status.Pending+status.Queued != 0 {
			t.Fatal("explicit neutralization requires initially empty pools")
		}
	}
	var saved types.Transaction
	requireNoError(t, saved.UnmarshalBinary(source.Stopped.Purchases[0].Saved))
	if saved.Nonce() != 39 || source.Stopped.Purchases[0].Nonce != 8 {
		t.Fatal("expected nonce gap 8 through 38")
	}
	purchase := common.BuyTicketParam{Start: head.Time() - 2*24*3600, End: head.Time() + 28*24*3600}
	body, err := rlp.EncodeToBytes(&purchase)
	requireNoError(t, err)
	data, err := rlp.EncodeToBytes(&common.FSNCallParam{Func: common.BuyTicketFunc, Data: body})
	requireNoError(t, err)
	probe := signNeutralizationRPC(t, nodes[0], owner, common.FSNCallAddress, 8, 100000, data)
	var returned common.Hash
	probeRaw, err := probe.MarshalBinary()
	requireNoError(t, err)
	admission := nodes[1].call(t, &returned, "eth_sendRawTransaction", hexutil.Bytes(probeRaw))
	requireErrorContains(t, admission, "BuyTicket end must be greater than latest block time + 1 month")
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "expired-probe.json"), map[string]interface{}{
		"Head": head.Header(), "Purchase": purchase, "Transaction": probe, "Raw": hexutil.Bytes(probeRaw),
		"PoolError": admission.Error(), "HistoricalOriginal": false, "SavedIntentChanged": false,
	}))
	var transfers types.Transactions
	for nonce := uint64(8); nonce < saved.Nonce(); nonce++ {
		tx := signNeutralizationRPC(t, nodes[0], owner, owner, nonce, 21000, nil)
		if tx.Nonce() != nonce || tx.To() == nil || *tx.To() != owner || tx.Value().Sign() != 0 || tx.Gas() != 21000 || len(tx.Data()) != 0 {
			t.Fatal("signed self-transfer differs from explicit nonce plan")
		}
		transfers = append(transfers, tx)
	}
	encoded, err := rlp.EncodeToBytes(transfers)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(root, "neutralizations.rlp"), encoded, 0600))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "neutralizations.json"), transfers))
	for _, tx := range transfers {
		data, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, nodes[1].call(t, &returned, "eth_sendRawTransaction", hexutil.Bytes(data)))
		if returned != tx.Hash() {
			t.Fatal("recipient changed reviewed self-transfer identity")
		}
	}
	var recipient deliveryPoolState
	requireNoError(t, nodes[1].call(t, &recipient, "lab_deliveryPool"))
	if len(recipient.Pending[owner]) != 31 || len(recipient.Queued[owner]) != 0 {
		t.Fatal("recipient did not admit every explicit nonce in sequence")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "recipient-before-mining.json"), recipient))
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	startCompetingMiner(t, nodes[1])
	awaitRehearsal(t, 90*time.Second, func() bool {
		return readPeerPurchase(t, nodes[0]).Nonce == 39 && readPeerPurchase(t, nodes[1]).Nonce >= 42 && nodes[0].status(t).Hash == nodes[1].status(t).Hash
	})
	var receipts [2]types.Receipts
	for i, node := range nodes {
		for _, tx := range transfers {
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if receipt == nil || receipt.TxHash != tx.Hash() || receipt.Status != types.ReceiptStatusSuccessful || receipt.GasUsed != 21000 || len(receipt.Logs) != 0 || readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64()).Hash() != receipt.BlockHash {
				t.Fatal("self-transfer lacks successful canonical receipt")
			}
			receipts[i] = append(receipts[i], receipt)
		}
	}
	startHeldPurchaseWorker(t, nodes[0])
	observed := time.Now()
	var samples []map[string]interface{}
	for time.Since(observed) < 12*time.Second {
		state := readPeerPurchase(t, nodes[0])
		if state.Nonce != 39 || !bytes.Equal(state.Saved, source.Stopped.Purchases[0].Saved) || len(state.Pending)+len(state.Queued) != 0 {
			t.Fatal("buyer rewrote intent, signed around it or admitted an unfunded purchase")
		}
		samples = append(samples, map[string]interface{}{"ObservedUTC": time.Now().UTC(), "Purchase": state, "Node": nodes[0].status(t)})
		time.Sleep(time.Second)
	}
	stopPeerAutoMiner(t, nodes[0])
	stopPeerAutoMiner(t, nodes[1])
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		node.stop(t, false)
	}
	requirePurchaseLogContains(t, paths[0], "insufficient balance")
	if stopped[0].Nonce != 39 || !bytes.Equal(stopped[0].Saved, source.Stopped.Purchases[0].Saved) {
		t.Fatal("explicit consumption changed the saved nonce-39 intent")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "neutralization-result.json"), map[string]interface{}{
		"Before": head.Header(), "Final": final.Header(), "Receipts": receipts, "BuyerSamples": samples,
		"NonceBefore": uint64(8), "NonceAfter": stopped[0].Nonce, "Saved": hexutil.Bytes(source.Stopped.Purchases[0].Saved),
		"NewFunding": false, "AutomaticReplacement": false, "PurchasesRestored": false, "ExpiredProbeWasHistoricalOriginal": false,
	}))
	t.Logf("31 explicit zero-value self-transfers consumed nonces 8..38; original nonce-39 intent preserved; enabled buyer remains unfunded; final=%d %s", final.NumberU64(), final.Hash().Hex())
}

func signNeutralizationRPC(t *testing.T, node *rehearsalNode, owner, to common.Address, nonce, gas uint64, data []byte) *types.Transaction {
	t.Helper()
	var signed struct {
		Raw hexutil.Bytes
		Tx  *types.Transaction
	}
	args := map[string]interface{}{"from": owner, "to": to, "nonce": hexutil.Uint64(nonce), "gas": hexutil.Uint64(gas), "gasPrice": (*hexutil.Big)(big.NewInt(2000000000)), "value": "0x0", "data": hexutil.Bytes(data)}
	requireNoError(t, node.call(t, &signed, "eth_signTransaction", args))
	var tx types.Transaction
	requireNoError(t, tx.UnmarshalBinary(signed.Raw))
	sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), &tx)
	requireNoError(t, err)
	if signed.Tx == nil || tx.Hash() != signed.Tx.Hash() || sender != owner {
		t.Fatal("RPC signature does not match reviewed synthetic account")
	}
	return &tx
}

func TestFullStateNonceNeutralizationColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	data, err := os.ReadFile(filepath.Join(root, "neutralizations.rlp"))
	requireNoError(t, err)
	var transfers types.Transactions
	requireNoError(t, rlp.DecodeBytes(data, &transfers))
	owner := common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf")
	if len(transfers) != 31 {
		t.Fatal("cold audit requires exactly 31 explicitly listed self-transfers")
	}
	for i, tx := range transfers {
		sender, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
		requireNoError(t, err)
		if sender != owner || tx.To() == nil || *tx.To() != owner || tx.Value().Sign() != 0 || len(tx.Data()) != 0 || tx.Nonce() != uint64(i+8) {
			t.Fatal("unexpected transaction in neutralization allowlist")
		}
	}
	auditRetainedPartitionCold(t, root, transfers)
	t.Logf("cold ledger allowed only %d named zero-value self-transfers; their gas, account nonces and all interval rights audited", len(transfers))
}
