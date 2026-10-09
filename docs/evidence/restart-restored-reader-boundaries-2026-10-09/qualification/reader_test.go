package recovery

import (
	"encoding/hex"
	"encoding/json"
	"math/big"
	"reflect"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestRestoredStartupReaderBoundaries(t *testing.T) {
	for _, test := range []struct {
		name, wantError                                       string
		foreignGenesis, wrongChain, changedFork, missingState bool
	}{
		{name: "complete_mainnet"},
		{name: "empty_database", wantError: "missing DaTong chain configuration"},
		{name: "missing_datong", wantError: "missing DaTong chain configuration"},
		{name: "split_heads", wantError: "full, header, fast and canonical heads must agree"},
		{name: "missing_head_header", wantError: "full, header, fast and canonical heads must agree"},
		{name: "foreign_genesis_same_chain_id", foreignGenesis: true},
		{name: "wrong_chain_id", wrongChain: true},
		{name: "changed_fork_config", changedFork: true},
		{name: "missing_head_state", missingState: true},
		{name: "missing_head_body"},
	} {
		test := test
		t.Run(test.name, func(t *testing.T) {
			db := rawdb.NewMemoryDatabase()
			defer db.Close()
			if test.name != "empty_database" {
				genesis := core.DefaultGenesisBlock()
				config := *genesis.Config
				genesis.Config = &config
				if test.foreignGenesis {
					genesis.ExtraData = []byte("different synthetic network")
				}
				block, err := genesis.Commit(db)
				if err != nil {
					t.Fatal(err)
				}
				if (block.Hash() != params.MainnetGenesisHash) != test.foreignGenesis {
					t.Fatal("fixture genesis identity differs from declared case")
				}
				rawdb.WriteHeadFastBlockHash(db, block.Hash())
				switch test.name {
				case "missing_datong":
					config.DaTong = nil
				case "split_heads":
					rawdb.WriteHeadHeaderHash(db, common.HexToHash("0x01"))
				case "missing_head_header":
					rawdb.DeleteHeader(db, block.Hash(), 0)
				case "wrong_chain_id":
					config.ChainID = big.NewInt(1)
				case "changed_fork_config":
					config.HomesteadBlock = big.NewInt(1)
				case "missing_head_body":
					rawdb.DeleteBody(db, block.Hash(), 0)
				case "missing_head_state":
					if present, err := db.Has(block.Root().Bytes()); err != nil || !present {
						t.Fatal("fixture state root must exist before removal", err)
					}
					if err := db.Delete(block.Root().Bytes()); err != nil {
						t.Fatal(err)
					}
				}
				rawdb.WriteChainConfig(db, block.Hash(), &config)
			}
			before := readerDatabaseContents(t, db)

			reader, err := NewReader(db)

			if test.wantError != "" {
				if err == nil || !strings.Contains(err.Error(), test.wantError) {
					t.Fatalf("want refusal %q, got %v", test.wantError, err)
				}
			} else {
				if err != nil {
					t.Fatal(err)
				}
				if (reader.Config().ChainID.Cmp(big.NewInt(32659)) != 0) != test.wrongChain {
					t.Fatal("reader chain ID differs from fixture")
				}
				if (reader.Config().HomesteadBlock.Cmp(big.NewInt(0)) != 0) != test.changedFork {
					t.Fatal("reader fork schedule differs from fixture")
				}
				head := reader.CurrentHeader()
				_, stateErr := reader.StateAt(head.Root, head.MixDigest)
				if (stateErr != nil) != test.missingState {
					t.Fatalf("state availability differs: %v", stateErr)
				}
				if (reader.GetBlock(head.Hash(), 0) == nil) != (test.name == "missing_head_body") {
					t.Fatal("body availability differs from fixture")
				}
			}
			if !reflect.DeepEqual(before, readerDatabaseContents(t, db)) {
				t.Fatal("reader observation mutated database contents")
			}
			observation := map[string]interface{}{"case": test.name, "reader_accepted": err == nil, "database_unchanged": true, "foreign_genesis": test.foreignGenesis, "wrong_chain_id": test.wrongChain, "changed_fork_config": test.changedFork, "missing_head_state": test.missingState, "missing_head_body": test.name == "missing_head_body"}
			encoded, err := json.Marshal(observation)
			if err != nil {
				t.Fatal(err)
			}
			t.Logf("reader boundary observation: %s", encoded)
		})
	}
}

func readerDatabaseContents(t *testing.T, db ethdb.Database) map[string]string {
	t.Helper()
	contents := make(map[string]string)
	iterator := db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		contents[hex.EncodeToString(iterator.Key())] = hex.EncodeToString(iterator.Value())
	}
	if err := iterator.Error(); err != nil {
		t.Fatal(err)
	}
	return contents
}
