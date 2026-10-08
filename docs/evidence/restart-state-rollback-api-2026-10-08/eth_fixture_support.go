package eth

import (
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/eth/ethconfig"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/miner"
	"time"
)

func F11FixtureBackend(chain *core.BlockChain, db ethdb.Database, pending *miner.Miner) *EthAPIBackend {
	return &EthAPIBackend{eth: &Ethereum{blockchain: chain, chainDb: db, engine: chain.Engine(), miner: pending, config: &ethconfig.Config{RPCGasCap: 1000000, RPCEVMTimeout: 2 * time.Second}}}
}
