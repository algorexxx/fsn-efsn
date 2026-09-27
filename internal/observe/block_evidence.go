package observe

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type BlockEvidence struct {
	RLP      hexutil.Bytes
	Receipts types.Receipts
}

func (reader readClient) blockEvidence(ctx context.Context, number uint64) (BlockEvidence, error) {
	var result BlockEvidence
	var raw json.RawMessage
	if err := reader.call(ctx, &raw, "eth_getBlockByNumber", hexutil.EncodeUint64(number), false); err != nil {
		return result, err
	}
	var header *types.Header
	var fields struct {
		Hash         common.Hash
		Transactions []common.Hash
		Uncles       []common.Hash
	}
	if json.Unmarshal(raw, &header) != nil || json.Unmarshal(raw, &fields) != nil || header == nil || header.Number == nil || !header.Number.IsUint64() || header.Number.Uint64() != number || header.Hash() != fields.Hash || fields.Transactions == nil || fields.Uncles == nil || len(fields.Uncles) != 0 || len(fields.Transactions) > 4096 {
		return result, fmt.Errorf("missing, invalid or unsupported block body")
	}
	txs := make([]*types.Transaction, 0, len(fields.Transactions))
	result.Receipts = make(types.Receipts, 0, len(fields.Transactions))
	bytesUsed := len(raw)
	for i, hash := range fields.Transactions {
		var signed hexutil.Bytes
		var receiptJSON json.RawMessage
		if err := reader.call(ctx, &signed, "eth_getRawTransactionByBlockHashAndIndex", fields.Hash, hexutil.Uint(i)); err != nil {
			return BlockEvidence{}, err
		}
		var tx types.Transaction
		if tx.UnmarshalBinary(signed) != nil || tx.Hash() != hash {
			return BlockEvidence{}, fmt.Errorf("transaction bytes differ from block")
		}
		if err := reader.call(ctx, &receiptJSON, "eth_getTransactionReceipt", hash); err != nil {
			return BlockEvidence{}, err
		}
		bytesUsed += len(signed) + len(receiptJSON)
		if bytesUsed > maxBackfillBytes {
			return BlockEvidence{}, fmt.Errorf("block response exceeds backfill limit")
		}
		var receipt *types.Receipt
		var presence struct {
			Status           *hexutil.Uint64
			Root             hexutil.Bytes
			TransactionIndex *hexutil.Uint
		}
		if json.Unmarshal(receiptJSON, &receipt) != nil || json.Unmarshal(receiptJSON, &presence) != nil || receipt == nil || presence.TransactionIndex == nil || (presence.Status == nil && len(presence.Root) != 32) {
			return BlockEvidence{}, fmt.Errorf("missing or incomplete receipt")
		}
		txs = append(txs, &tx)
		result.Receipts = append(result.Receipts, receipt)
	}
	block := types.NewBlockWithHeader(header).WithBody(txs, nil)
	var err error
	result.RLP, err = rlp.EncodeToBytes(block)
	return result, err
}

func validateBlockEvidence(evidence BlockEvidence) (*types.Block, error) {
	var block types.Block
	if len(evidence.RLP) > maxBackfillBytes || rlp.DecodeBytes(evidence.RLP, &block) != nil || block.Number() == nil || !block.Number().IsUint64() || len(block.Uncles()) != 0 || len(block.Transactions()) > 4096 || len(block.Transactions()) != len(evidence.Receipts) {
		return nil, fmt.Errorf("invalid or unsupported retained block")
	}
	if types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() {
		return nil, fmt.Errorf("transaction commitment mismatch")
	}
	var gas uint64
	var logIndex uint
	for i, receipt := range evidence.Receipts {
		tx := block.Transactions()[i]
		if receipt == nil || receipt.TxHash != tx.Hash() || receipt.Type != tx.Type() || receipt.BlockNumber == nil || receipt.BlockNumber.Cmp(block.Number()) != 0 || receipt.BlockHash != block.Hash() || receipt.TransactionIndex != uint(i) || (len(receipt.PostState) != 0 && len(receipt.PostState) != 32) || (len(receipt.PostState) == 0 && receipt.Status > types.ReceiptStatusSuccessful) || receipt.CumulativeGasUsed < gas || receipt.GasUsed != receipt.CumulativeGasUsed-gas {
			return nil, fmt.Errorf("receipt identity, outcome or gas mismatch")
		}
		gas = receipt.CumulativeGasUsed
		for _, log := range receipt.Logs {
			if log == nil || log.Removed || log.TxHash != tx.Hash() || log.TxIndex != uint(i) || log.BlockHash != block.Hash() || log.BlockNumber != block.NumberU64() || log.Index != logIndex {
				return nil, fmt.Errorf("log identity mismatch")
			}
			logIndex++
		}
		if types.CreateBloom(types.Receipts{receipt}) != receipt.Bloom {
			return nil, fmt.Errorf("receipt bloom mismatch")
		}
	}
	if gas != block.GasUsed() || types.CreateBloom(evidence.Receipts) != block.Bloom() || types.DeriveSha(evidence.Receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() {
		return nil, fmt.Errorf("receipt commitment mismatch")
	}
	return &block, nil
}
