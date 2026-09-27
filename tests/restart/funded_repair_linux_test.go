package restart

import (
	"bytes"
	"math/big"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func rehearseFundedSmallReserveRepair(t *testing.T) {
	requirePartitionNamespace(t)
	keyBytes := make([]byte, 32)
	keyBytes[31] = 3
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	funder := &fixture{key: key, owner: crypto.PubkeyToAddress(key.PublicKey)}
	allocation := core.GenesisAlloc{funder.owner: {Balance: decimal(t, "6000000000000000000000")}}
	pair := seedDenseMinerPairWithFunding(t, "12020102000000000000000", 2, allocation)
	rehearsePartitionRepairWithPair(t, pair, funder)
}

func fundLivePurchaseRepair(t *testing.T, nodes [2]*rehearsalNode, funder *fixture, purchase *types.Transaction, recipient common.Address) *types.Transaction {
	t.Helper()
	if purchase == nil {
		t.Fatal("original missing purchase is required before funding")
	}
	validateLiveRepairPurchase(t, nodes[0], purchase)
	raw, err := purchase.MarshalBinary()
	requireNoError(t, err)
	var hash common.Hash
	err = nodes[0].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw))
	if err == nil || !strings.Contains(err.Error(), "insufficient balance") {
		t.Fatalf("funding experiment requires the unfunded purchase rejection, got %v", err)
	}
	t.Logf("funded repair confirmed original purchase rejection: %v", err)
	var nonce hexutil.Uint64
	requireNoError(t, nodes[0].call(t, &nonce, "eth_getTransactionCount", funder.owner, "pending"))
	if nonce != 0 {
		t.Fatal("funding wallet already used")
	}
	transfer, err := types.SignTx(types.NewTransaction(0, recipient, decimal(t, "5000000000000000000000"), 21000, big.NewInt(1000000000), nil), types.LatestSignerForChainID(purchase.ChainId()), funder.key)
	requireNoError(t, err)
	raw, err = transfer.MarshalBinary()
	requireNoError(t, err)
	requireNoError(t, nodes[0].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw)))
	if hash != transfer.Hash() {
		t.Fatal("funding transfer identity changed")
	}
	awaitLiveFundingTransfer(t, nodes, transfer)
	validateLiveRepairPurchase(t, nodes[0], purchase)
	return transfer
}

func awaitLiveFundingTransfer(t *testing.T, nodes [2]*rehearsalNode, transfer *types.Transaction) *types.Receipt {
	t.Helper()
	hash := transfer.Hash()
	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		requireContinuousMiners(t, nodes[0], nodes[1])
		var receipts [2]*types.Receipt
		for i, node := range nodes {
			requireNoError(t, node.call(t, &receipts[i], "eth_getTransactionReceipt", hash))
		}
		if receipts[0] != nil && receipts[1] != nil && receipts[0].BlockHash == receipts[1].BlockHash {
			for i, receipt := range receipts {
				if receipt.Status != types.ReceiptStatusSuccessful || receipt.GasUsed != 21000 || receipt.TxHash != hash || readRecoveryNodeBlock(t, nodes[i], receipt.BlockNumber.Uint64()).Hash() != receipt.BlockHash {
					t.Fatal("funding transfer was not canonical and successful on both nodes")
				}
			}
			t.Logf("funded repair transfer value-wei=%s hash=%s block=%d %s gas=21000", transfer.Value(), hash.Hex(), receipts[0].BlockNumber.Uint64(), receipts[0].BlockHash.Hex())
			return receipts[0]
		}
		time.Sleep(250 * time.Millisecond)
	}
	t.Fatal("funding transfer did not reach canonical success on both nodes")
	return nil
}

func requireColdRepairFunding(t *testing.T, node *rehearsalNode, owner common.Address, transfer *types.Transaction) {
	t.Helper()
	var receipt *types.Receipt
	var balance string
	var nonce hexutil.Uint64
	requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", transfer.Hash()))
	requireNoError(t, node.call(t, &balance, "fsn_getBalance", common.SystemAssetID, owner, "latest"))
	requireNoError(t, node.call(t, &nonce, "eth_getTransactionCount", owner, "latest"))
	if receipt == nil || receipt.Status != types.ReceiptStatusSuccessful || receipt.GasUsed != 21000 || receipt.TxHash != transfer.Hash() || nonce != 1 || balance != "999999979000000000000" {
		t.Fatal("cold funding receipt, single sender nonce or exact 6000 minus 5000 minus fee balance differs")
	}
	if readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64()).Hash() != receipt.BlockHash {
		t.Fatal("cold funding receipt is not canonical")
	}
	t.Logf("funded repair cold transfer=%s sponsor-nonce=%d sponsor-liquid-wei=%s", transfer.Hash().Hex(), nonce, balance)
}

func submitFundedRepairPurchase(t *testing.T, nodes [2]*rehearsalNode, gap livePurchaseGap, tx *types.Transaction, owners []common.Address) common.Hash {
	t.Helper()
	raw, err := tx.MarshalBinary()
	requireNoError(t, err)
	saved, err := gap.saved.MarshalBinary()
	requireNoError(t, err)
	started := time.Now()
	for time.Since(started) < 120*time.Second {
		requireContinuousMiners(t, nodes[0], nodes[1])
		state := readPeerPurchase(t, nodes[gap.index])
		if state.Nonce != tx.Nonce() || !bytes.Equal(state.Saved, saved) || len(state.Pending)+len(state.Queued) != 0 {
			t.Fatal("nonce, saved intent or pool changed while waiting for purchase funding")
		}
		var hash common.Hash
		err = nodes[gap.index].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw))
		if err == nil {
			t.Logf("funded repair admitted original nonce=%d hash=%s after-wait=%s", tx.Nonce(), hash.Hex(), time.Since(started))
			return hash
		}
		if !strings.Contains(err.Error(), "insufficient balance") {
			t.Fatalf("purchase submission failed for a reason other than funding: %v", err)
		}
		t.Logf("funded repair waiting for ordinary ticket return nonce=%d elapsed=%s rejection=%v", tx.Nonce(), time.Since(started), err)
		time.Sleep(2 * time.Second)
	}
	validateLiveRepairPurchase(t, nodes[gap.index], tx)
	head := nodes[gap.index].status(t).Number
	auditPartitionFunds(t, nodes[gap.index], owners, 24, head, "funding-timeout")
	logContinuousPurchaseState(t, nodes[0], nodes[1])
	t.Fatalf("original purchase still unfunded after bounded 120-second wait: %v", err)
	return common.Hash{}
}
