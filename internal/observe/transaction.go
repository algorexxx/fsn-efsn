package observe

import (
	"bytes"
	"context"
	"encoding/json"
	"math/big"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func observeTransaction(ctx context.Context, reader readClient, node *Observation, tx *types.Transaction, raw []byte, now time.Time) TransactionObservation {
	result := TransactionObservation{Hash: tx.Hash(), Nonce: tx.Nonce(), Owner: node.Wallet, Raw: raw, Pool: "unknown", Inclusion: "unknown", Payload: "not_a_purchase", Funding: "not_a_purchase", NonceRelation: "unknown"}
	if node.PoolKnown {
		result.Pool = "absent"
		for _, entry := range node.Pool {
			if entry.Transaction.Hash() == tx.Hash() {
				result.Pool = entry.Queue
			}
			if entry.Transaction.Nonce() == tx.Nonce() && entry.Transaction.Hash() != tx.Hash() {
				result.Pool = "conflicting_nonce"
				break
			}
		}
	}
	if node.Nonce != nil {
		result.NonceRelation = "current"
		if tx.Nonce() > uint64(*node.Nonce) {
			result.NonceRelation = "ahead"
		}
		if tx.Nonce() < uint64(*node.Nonce) {
			result.NonceRelation = "consumed"
		}
	}
	if tx.To() != nil && *tx.To() == common.FSNCallAddress {
		result.Payload, result.Funding = "invalid_or_unsupported_native_payload", "unknown"
		var envelope common.FSNCallParam
		if rlp.DecodeBytes(tx.Data(), &envelope) == nil && envelope.Func == common.BuyTicketFunc {
			result.Purchase, result.Payload, result.Funding = true, "invalid", "unknown"
			var interval common.BuyTicketParam
			if rlp.DecodeBytes(envelope.Data, &interval) == nil {
				result.Interval = &interval
				if interval.Check(node.Head.Header.Number, node.Head.Header.Time) == nil && tx.Value().Sign() == 0 && now.Unix() >= 0 && interval.End > uint64(now.Unix()) {
					result.Payload = "valid_at_observation"
					if node.Head.Header.BaseFee != nil && tx.GasPrice().Cmp(node.Head.Header.BaseFee) < 0 {
						result.Payload = "below_base_fee"
					}
					assessFunding(node, tx, &result, uint64(now.Unix()))
				}
			}
		}
	}
	receiptJSON := json.RawMessage("null")
	if !node.read(ctx, reader, &receiptJSON, "eth_getTransactionReceipt", tx.Hash()) {
		return result
	}
	var status struct{ Status *hexutil.Uint64 }
	if json.Unmarshal(receiptJSON, &result.Receipt) != nil || json.Unmarshal(receiptJSON, &status) != nil {
		node.issue("receipt:"+tx.Hash().Hex(), "invalid")
		return result
	}
	if result.Receipt == nil {
		result.Inclusion = "absent"
		return result
	}
	if status.Status == nil || uint64(*status.Status) > types.ReceiptStatusSuccessful {
		node.issue("receipt:"+tx.Hash().Hex(), "invalid_or_missing_status")
		return result
	}
	receipt := result.Receipt
	if receipt.TxHash != tx.Hash() || receipt.BlockNumber == nil || !receipt.BlockNumber.IsUint64() || receipt.BlockNumber.Uint64() > node.Head.Header.Number.Uint64() {
		node.issue("receipt:"+tx.Hash().Hex(), "outside_observation_or_invalid")
		return result
	}
	block := node.readBlock(ctx, reader, hexutil.EncodeUint64(receipt.BlockNumber.Uint64()))
	if block == nil {
		return result
	}
	if block.Hash != receipt.BlockHash {
		result.Inclusion = "noncanonical"
		return result
	}
	var included hexutil.Bytes
	if !node.read(ctx, reader, &included, "eth_getRawTransactionByBlockHashAndIndex", receipt.BlockHash, hexutil.Uint64(receipt.TransactionIndex)) {
		return result
	}
	if !bytes.Equal(included, raw) {
		node.issue("receipt:"+tx.Hash().Hex(), "transaction_mismatch")
		return result
	}
	result.Inclusion = "canonical_failed"
	if receipt.Status != types.ReceiptStatusSuccessful {
		return result
	}
	result.Inclusion = "canonical_ordinary_success"
	if !result.Purchase {
		if tx.To() != nil && *tx.To() == common.FSNCallAddress {
			result.Inclusion = "native_success_unverified"
		}
		return result
	}
	result.Inclusion = "native_success_unverified"
	expected := crypto.Keccak256Hash(node.Wallet[:], block.Header.ParentHash[:])
	valid := 0
	for _, log := range receipt.Logs {
		if log == nil {
			return result
		}
		if log.Address != common.FSNCallAddress || len(log.Topics) == 0 || log.Topics[0] != common.BytesToHash([]byte{byte(common.BuyTicketFunc)}) {
			continue
		}
		if log.Removed || log.TxHash != tx.Hash() || log.BlockHash != receipt.BlockHash || log.BlockNumber != receipt.BlockNumber.Uint64() || log.TxIndex != receipt.TransactionIndex {
			return result
		}
		var outcome struct {
			TicketID    common.Hash
			TicketOwner common.Address
			Error       string
		}
		if json.Unmarshal(log.Data, &outcome) != nil || outcome.Error != "" {
			result.Inclusion = "native_failed"
			return result
		}
		if outcome.TicketID != expected || outcome.TicketOwner != node.Wallet {
			return result
		}
		valid++
	}
	if valid != 1 {
		return result
	}
	var tickets map[common.Hash]common.TicketDisplay
	if !node.read(ctx, reader, &tickets, "fsn_allTicketsByAddress", node.Wallet, hexutil.EncodeUint64(receipt.BlockNumber.Uint64())) {
		return result
	}
	ticket, exists := tickets[expected]
	if exists && result.Interval != nil && ticket.Owner == node.Wallet && ticket.Height == receipt.BlockNumber.Uint64() && ticket.StartTime == result.Interval.Start && ticket.ExpireTime == result.Interval.End && ticket.Value != nil && ticket.Value.Cmp(common.TicketPrice(receipt.BlockNumber)) == 0 {
		result.Inclusion = "canonical_native_success"
	}
	return result
}

func assessFunding(node *Observation, tx *types.Transaction, result *TransactionObservation, now uint64) {
	if node.LiquidWei == nil || node.TimeLocks == nil || result.Interval == nil {
		return
	}
	liquid, ok := new(big.Int).SetString(*node.LiquidWei, 10)
	if !ok {
		return
	}
	start := common.MaxUint64(result.Interval.Start, now)
	coverage := node.TimeLocks.GetSpendableValue(start, result.Interval.End)
	needed := new(big.Int).Mul(new(big.Int).SetUint64(tx.Gas()), tx.GasPrice())
	if coverage.Cmp(common.TicketPrice(node.Head.Header.Number)) < 0 {
		needed.Add(needed, common.TicketPrice(node.Head.Header.Number))
	}
	result.CoverageWei, result.RequiredLiquidWei = coverage.String(), needed.String()
	result.Funding = "available_estimate"
	if liquid.Cmp(needed) < 0 {
		result.Funding = "insufficient_estimate"
	}
}
