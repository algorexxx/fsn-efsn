package restart

import (
	"bytes"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

type displacedPurchaseBlock struct {
	Hash         common.Hash
	Number       hexutil.Uint64
	Transactions []common.Hash
}

func requireDisplacedPurchaseRPC(t *testing.T, node *rehearsalNode, old *types.Block, original *types.Transaction) *types.Transaction {
	t.Helper()
	var byHash hexutil.Bytes
	requireNoError(t, node.call(t, &byHash, "eth_getRawTransactionByHash", original.Hash()))
	if len(byHash) != 0 {
		t.Fatal("displaced purchase unexpectedly remains in canonical lookup or pool")
	}
	var block *displacedPurchaseBlock
	requireNoError(t, node.call(t, &block, "eth_getBlockByHash", old.Hash(), false))
	if block == nil || block.Hash != old.Hash() || uint64(block.Number) != old.NumberU64() {
		t.Fatal("stored displaced block is unavailable by its original hash")
	}
	index := -1
	for i, hash := range block.Transactions {
		if hash == original.Hash() {
			index = i
		}
	}
	if index < 0 {
		t.Fatal("displaced block does not contain the original purchase")
	}
	var raw hexutil.Bytes
	requireNoError(t, node.call(t, &raw, "eth_getRawTransactionByBlockHashAndIndex", old.Hash(), hexutil.Uint64(index)))
	expected, err := original.MarshalBinary()
	requireNoError(t, err)
	if !bytes.Equal(raw, expected) {
		t.Fatal("block-hash lookup did not recover the exact signed bytes")
	}
	var recovered types.Transaction
	requireNoError(t, recovered.UnmarshalBinary(raw))
	if recovered.Hash() != original.Hash() || recovered.Nonce() != original.Nonce() {
		t.Fatal("decoded displaced purchase identity differs")
	}
	var canonical *displacedPurchaseBlock
	requireNoError(t, node.call(t, &canonical, "eth_getBlockByNumber", hexutil.EncodeUint64(old.NumberU64()), false))
	if canonical == nil || canonical.Hash == old.Hash() {
		t.Fatal("old block is still canonical")
	}
	var receipt *types.Receipt
	requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", recovered.Hash()))
	if receipt != nil {
		t.Fatal("retrieving old signed bytes incorrectly supplied a canonical receipt")
	}
	for _, request := range []struct {
		hash  common.Hash
		index hexutil.Uint64
	}{{old.Hash(), hexutil.Uint64(len(block.Transactions))}, {common.Hash{}, 0}} {
		var missing hexutil.Bytes
		requireNoError(t, node.call(t, &missing, "eth_getRawTransactionByBlockHashAndIndex", request.hash, request.index))
		if len(missing) != 0 {
			t.Fatal("missing block or out-of-range transaction index returned data")
		}
	}
	t.Logf("displaced purchase RPC recovered nonce=%d hash=%s bytes=%d old-block=%d %s index=%d replacement=%s; transaction-hash lookup and receipt absent; invalid locations return null", recovered.Nonce(), recovered.Hash().Hex(), len(raw), old.NumberU64(), old.Hash().Hex(), index, canonical.Hash.Hex())
	return &recovered
}
