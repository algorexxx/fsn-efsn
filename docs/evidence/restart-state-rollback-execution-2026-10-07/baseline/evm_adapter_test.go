package state_test

import (
	"github.com/FusionFoundation/efsn/v5/params"
)

const f11Candidate = false

func f11ExecutionConfig(scheduled, london bool) *params.ChainConfig {
	config := *params.MainnetChainConfig
	if !london {
		config.LondonBlock = nil
	}
	return &config
}
