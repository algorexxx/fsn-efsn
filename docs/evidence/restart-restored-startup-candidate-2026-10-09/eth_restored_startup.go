package eth

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/eth/downloader"
	"github.com/FusionFoundation/efsn/v5/eth/ethconfig"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/params"
)

func checkRestoredStartup(stack *node.Node, config *ethconfig.Config) error {
	expected, genesis := params.MainnetChainConfig, params.MainnetGenesisHash
	if config.Genesis != nil {
		expected = config.Genesis.Config
		if expected == nil {
			return fmt.Errorf("restored startup: missing genesis configuration")
		}
		genesis = config.Genesis.ToBlock(nil).Hash()
	}
	anchor, err := expected.RestartAnchorForGenesis(genesis)
	if err != nil || anchor == nil {
		return err
	}
	if config.SyncMode != downloader.FullSync {
		return fmt.Errorf("restored startup: full sync required")
	}
	if stack.Config().DataDir == "" {
		return fmt.Errorf("restored startup: persistent restored datadir required")
	}
	if _, err := os.Stat(filepath.Join(stack.ResolvePath("chaindata"), "CURRENT")); err != nil {
		return fmt.Errorf("restored startup: existing database required: %w", err)
	}
	db, err := stack.OpenDatabase("chaindata", config.DatabaseCache, config.DatabaseHandles, "eth/db/preflight/", true)
	if err != nil {
		return fmt.Errorf("restored startup: read-only database open: %w", err)
	}
	checkErr := core.CheckRestoredState(db, expected, genesis)
	closeErr := db.Close()
	if checkErr != nil {
		return checkErr
	}
	return closeErr
}
