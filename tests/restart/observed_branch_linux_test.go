package restart

import (
	"bytes"
	"os"
	"sort"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func captureObservedBranch(t *testing.T, node *rehearsalNode, hash common.Hash, floor uint64, retained map[common.Hash]*types.Block) {
	t.Helper()
	for retained[hash] == nil {
		var data hexutil.Bytes
		requireNoError(t, node.call(t, &data, "lab_blockByHash", hash))
		var block *types.Block
		requireNoError(t, rlp.DecodeBytes(data, &block))
		if block == nil || block.Hash() != hash {
			t.Fatal("observed block lookup changed identity")
		}
		if block.NumberU64() <= floor {
			return
		}
		retained[hash] = block
		hash = block.ParentHash()
	}
}

func retainObservedBlocks(t *testing.T, path string, retained map[common.Hash]*types.Block) types.Blocks {
	t.Helper()
	blocks := make(types.Blocks, 0, len(retained))
	for _, block := range retained {
		blocks = append(blocks, block)
	}
	sort.Slice(blocks, func(i, j int) bool {
		if blocks[i].NumberU64() != blocks[j].NumberU64() {
			return blocks[i].NumberU64() < blocks[j].NumberU64()
		}
		return bytes.Compare(blocks[i].Hash().Bytes(), blocks[j].Hash().Bytes()) < 0
	})
	encoded, err := rlp.EncodeToBytes(blocks)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(path, encoded, 0600))
	return blocks
}
