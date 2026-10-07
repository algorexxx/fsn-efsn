package params

import (
	"fmt"
	"math/big"

	"github.com/FusionFoundation/efsn/v5/common"
)

func (c *ChainConfig) IsSuicideTimeLockFix(number *big.Int) bool {
	return isForked(c.SuicideTimeLockFixBlock, number)
}

func (c *ChainConfig) CheckSuicideTimeLockFixCompatible(next *ChainConfig, height uint64) *ConfigCompatError {
	if isForkIncompatible(c.SuicideTimeLockFixBlock, next.SuicideTimeLockFixBlock, new(big.Int).SetUint64(height)) {
		return newCompatError("Suicide time-lock fix block", c.SuicideTimeLockFixBlock, next.SuicideTimeLockFixBlock)
	}
	return nil
}

func ResolveSuicideTimeLockFix(config *ChainConfig, genesis common.Hash, height uint64) (*ChainConfig, error) {
	if config == nil {
		return nil, fmt.Errorf("suicide time-lock fix: chain configuration required")
	}
	if config.SuicideTimeLockFixBlock != nil && !config.SuicideTimeLockFixBlock.IsUint64() {
		return nil, fmt.Errorf("suicide time-lock fix: activation height must fit uint64")
	}
	resolved := *config
	if config.SuicideTimeLockFixBlock != nil {
		resolved.SuicideTimeLockFixBlock = new(big.Int).Set(config.SuicideTimeLockFixBlock)
	}
	if genesis != MainnetGenesisHash {
		return &resolved, nil
	}
	if config.ChainID == nil || config.ChainID.Cmp(MainnetChainConfig.ChainID) != 0 {
		return nil, fmt.Errorf("suicide time-lock fix: mainnet chain identity mismatch")
	}
	approved := MainnetChainConfig.SuicideTimeLockFixBlock
	if approved == nil {
		if config.SuicideTimeLockFixBlock != nil {
			return nil, fmt.Errorf("suicide time-lock fix: no mainnet activation is approved in this build")
		}
		return &resolved, nil
	}
	if !approved.IsUint64() || approved.Sign() <= 0 {
		return nil, fmt.Errorf("suicide time-lock fix: invalid approved mainnet activation")
	}
	if config.SuicideTimeLockFixBlock != nil {
		if config.SuicideTimeLockFixBlock.Cmp(approved) != 0 {
			return nil, fmt.Errorf("suicide time-lock fix: mainnet activation differs from this build")
		}
		return &resolved, nil
	}
	if height >= approved.Uint64() {
		return nil, fmt.Errorf("suicide time-lock fix: missing mainnet activation at or after its boundary")
	}
	resolved.SuicideTimeLockFixBlock = new(big.Int).Set(approved)
	return &resolved, nil
}
