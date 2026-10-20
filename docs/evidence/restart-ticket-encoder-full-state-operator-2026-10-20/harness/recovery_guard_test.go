package restart

import (
	"testing"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func recoveryPlan(t *testing.T, signer, buyer *fixture, timestamp, next uint64, tx *types.Transaction) recovery.Plan {
	t.Helper()
	var call common.FSNCallParam
	var purchase common.BuyTicketParam
	requireNoError(t, rlp.DecodeBytes(tx.Data(), &call))
	requireNoError(t, rlp.DecodeBytes(call.Data, &purchase))
	parent := signer.chain.CurrentBlock()
	return recovery.Plan{GenesisHash: signer.chain.Genesis().Hash(), ChainID: signer.chain.Config().ChainID.Uint64(), ParentNumber: parent.NumberU64(), ParentHash: parent.Hash(), Signer: signer.owner, Timestamp: timestamp, NextTimestamp: next, Purchase: recovery.Purchase{Hash: tx.Hash(), Owner: buyer.owner, Nonce: tx.Nonce(), Start: purchase.Start, End: purchase.End}}
}
