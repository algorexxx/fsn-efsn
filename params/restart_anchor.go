package params

import (
	"fmt"

	"github.com/FusionFoundation/efsn/v5/common"
)

type RestartAnchor struct {
	GenesisHash common.Hash
	ChainID     uint64
	Number      uint64
	Hash        common.Hash
}

func (c *ChainConfig) RestartAnchorForGenesis(genesis common.Hash) (*RestartAnchor, error) {
	anchor := c.RestartAnchor
	if genesis == MainnetGenesisHash {
		anchor = MainnetChainConfig.RestartAnchor
	}
	if anchor == nil {
		return nil, nil
	}
	if anchor.GenesisHash != genesis || c.ChainID == nil || !c.ChainID.IsUint64() || c.ChainID.Uint64() != anchor.ChainID {
		return nil, fmt.Errorf("restart anchor: network identity mismatch")
	}
	if anchor.Number == 0 || anchor.Hash == (common.Hash{}) {
		return nil, fmt.Errorf("restart anchor: missing height or hash")
	}
	copy := *anchor
	return &copy, nil
}
