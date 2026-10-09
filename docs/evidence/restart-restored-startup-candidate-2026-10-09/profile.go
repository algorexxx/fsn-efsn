package main

import (
	"encoding/json"
	"os"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/params"
)

func init() {
	var profile struct {
		Genesis common.Hash
		Config  *params.ChainConfig
		Anchor  *params.RestartAnchor
	}
	blob, err := os.ReadFile(os.Getenv("FUSION_STARTUP_TEST_PROFILE"))
	if err != nil {
		panic(err)
	}
	if err := json.Unmarshal(blob, &profile); err != nil {
		panic(err)
	}
	params.MainnetGenesisHash = profile.Genesis
	params.MainnetChainConfig = profile.Config
	params.MainnetChainConfig.RestartAnchor = profile.Anchor
}
