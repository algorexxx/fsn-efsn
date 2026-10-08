package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

type observation struct {
	Registered   common.Hash
	Direct       *types.Header
	Repeated     *types.Header
	Initialized  common.Hash
	Restarted    common.Hash
	Stored       common.Hash
	StoredHeader *types.Header
	Config       *params.ChainConfig
	HeadBlock    common.Hash
	HeadHeader   common.Hash
	HeadFast     common.Hash
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	result := observation{Registered: params.MainnetGenesisHash}
	if len(os.Args) == 1 {
		genesis := core.DefaultGenesisBlock()
		result.Direct = genesis.ToBlock(nil).Header()
		result.Repeated = genesis.ToBlock(nil).Header()
		db := rawdb.NewMemoryDatabase()
		defer db.Close()
		config, hash, err := core.SetupGenesisBlock(db, nil)
		if err != nil {
			return err
		}
		result.Config, result.Initialized = config, hash
		_, result.Restarted, err = core.SetupGenesisBlock(db, nil)
		if err != nil {
			return err
		}
		readIdentity(db, &result)
	} else if len(os.Args) == 2 {
		db, err := rawdb.NewLevelDBDatabase(os.Args[1], 16, 16, "f12-readonly", true)
		if err != nil {
			return err
		}
		defer db.Close()
		readIdentity(db, &result)
	} else {
		return fmt.Errorf("expected zero arguments or a stopped synthetic database path")
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}

func readIdentity(db ethdb.Database, result *observation) {
	result.Stored = rawdb.ReadCanonicalHash(db, 0)
	result.StoredHeader = rawdb.ReadHeader(db, result.Stored, 0)
	result.Config = rawdb.ReadChainConfig(db, result.Stored)
	result.HeadBlock = rawdb.ReadHeadBlockHash(db)
	result.HeadHeader = rawdb.ReadHeadHeaderHash(db)
	result.HeadFast = rawdb.ReadHeadFastBlockHash(db)
}
