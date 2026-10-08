package restart

import (
"crypto/sha256"
"encoding/binary"
"testing"
"time"
"github.com/FusionFoundation/efsn/v5/common"
"github.com/FusionFoundation/efsn/v5/core/types"
"github.com/FusionFoundation/efsn/v5/ethdb"
"github.com/FusionFoundation/efsn/v5/rlp"
)

func advancePurchaseFixture(t *testing.T, f, verifier *fixture) {
	t.Helper()
	jump := uint64(time.Now().Unix()) - 3600
	for i := 0; i < 14; i++ {
		timestamp := f.chain.CurrentBlock().Time() + 120
		if i == 2 {
			timestamp = jump
		}
		var txs []*types.Transaction
		if i > 0 {
			txs = append(txs, f.signPurchase(t, f.chain.CurrentBlock().Time(), common.TimeLockForever))
		}
		block := f.buildBlockWithTransactions(t, timestamp, txs)
		f.importBlock(t, block)
		if verifier != nil {
			verifier.importBlock(t, block)
		}
	}
}

func buildAnchorBranch(t *testing.T, f *fixture, count int, spacing uint64) types.Blocks {
	t.Helper()
	blocks := make(types.Blocks, 0, count)
	for i := 0; i < count; i++ {
		parent := f.chain.CurrentBlock()
		tx := f.signPurchase(t, parent.Time(), common.TimeLockForever)
		block := f.buildBlockWithTransactions(t, parent.Time()+spacing, []*types.Transaction{tx})
		f.importBlock(t, block)
		blocks = append(blocks, block)
	}
	return blocks
}

func roundTripBlocks(t *testing.T, blocks types.Blocks) types.Blocks {
	t.Helper()
	encoded, err := rlp.EncodeToBytes(blocks)
	requireNoError(t, err)
	var received types.Blocks
	requireNoError(t, rlp.DecodeBytes(encoded, &received))
	return received
}

func blockHeaders(blocks types.Blocks) []*types.Header {
	headers := make([]*types.Header, len(blocks))
	for i, block := range blocks {
		headers[i] = block.Header()
	}
	return headers
}

func databaseDigest(t *testing.T, db ethdb.Database) common.Hash {
	t.Helper()
	hash := sha256.New()
	iterator := db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		for _, value := range [][]byte{iterator.Key(), iterator.Value()} {
			requireNoError(t, binary.Write(hash, binary.BigEndian, uint64(len(value))))
			_, err := hash.Write(value)
			requireNoError(t, err)
		}
	}
	requireNoError(t, iterator.Error())
	return common.BytesToHash(hash.Sum(nil))
}

