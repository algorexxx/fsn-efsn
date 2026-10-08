package miner

import (
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func F11FixturePending(chain *core.BlockChain, block *types.Block, pending *state.StateDB) *Miner {
	return &Miner{worker: &worker{chain: chain, snapshotBlock: block, snapshotState: pending}}
}
