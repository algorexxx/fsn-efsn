package state_test

import (
	"github.com/FusionFoundation/efsn/v5/params"
	"math/big"
	"os"
)

const f11Candidate = true

func init() {
	if os.Getenv("F11_ORIGINAL_REGRESSION") == "active" {
		config := *params.MainnetChainConfig
		config.SuicideTimeLockFixBlock = big.NewInt(15130081)
		params.MainnetChainConfig = &config
	}
}

func f11ExecutionConfig(scheduled, london bool) *params.ChainConfig {
	config := *params.MainnetChainConfig
	config.SuicideTimeLockFixBlock = nil
	if scheduled {
		config.SuicideTimeLockFixBlock = big.NewInt(15130081)
	}
	if !london {
		config.LondonBlock = nil
	}
	return &config
}
