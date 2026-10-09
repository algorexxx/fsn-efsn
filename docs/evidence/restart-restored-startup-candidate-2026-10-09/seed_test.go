package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestPrepareRestoredStartup(t *testing.T) {
	directory := os.Getenv("FUSION_STARTUP_TEST_DIRECTORY")
	if directory == "" {
		t.Skip("requires a disposable fixture directory")
	}
	mode := os.Getenv("FUSION_STARTUP_TEST_CASE")
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "efsn", "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	f := newFixtureInDatabase(t, 0, db)
	genesis := f.chain.Genesis()
	profile := struct {
		Genesis common.Hash
		Config  *params.ChainConfig
		Anchor  *params.RestartAnchor
	}{genesis.Hash(), f.chain.Config(), &params.RestartAnchor{GenesisHash: genesis.Hash(), ChainID: 32659, Number: f.parent.NumberU64(), Hash: f.parent.Hash()}}
	if mode == "valid" {
		child := f.buildBlock(t, f.parent.Time()+15, false)
		encoded, err := rlp.EncodeToBytes(child)
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(directory, "child.rlp"), encoded, 0600))
		verifier := newFixture(t)
		verifier.importBlock(t, child)
		metadata, err := json.Marshal(map[string]interface{}{"parent": f.parent.Hash(), "parent_height": f.parent.NumberU64(), "child": child.Hash(), "child_height": child.NumberU64()})
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(directory, "expected.json"), metadata, 0600))
	}
	f.chain.Stop()
	stored := *profile.Config
	switch mode {
	case "wrong_genesis":
		rawdb.WriteCanonicalHash(db, common.HexToHash("0x01"), 0)
	case "wrong_chain_id":
		stored.ChainID = big.NewInt(1)
		rawdb.WriteChainConfig(db, genesis.Hash(), &stored)
	case "wrong_fork":
		stored.HomesteadBlock = big.NewInt(1)
		rawdb.WriteChainConfig(db, genesis.Hash(), &stored)
	case "missing_datong":
		stored.DaTong = nil
		rawdb.WriteChainConfig(db, genesis.Hash(), &stored)
	case "missing_header":
		rawdb.DeleteHeader(db, f.parent.Hash(), f.parent.NumberU64())
	case "missing_body":
		rawdb.DeleteBody(db, f.parent.Hash(), f.parent.NumberU64())
	case "missing_state":
		present, err := db.Has(f.parent.Root().Bytes())
		requireNoError(t, err)
		if !present {
			t.Fatal("fixture state root missing before deletion")
		}
		requireNoError(t, db.Delete(f.parent.Root().Bytes()))
	case "wrong_ticket_commitment":
		header := f.parent.Header()
		header.MixDigest = common.HexToHash("0x01")
		block := f.parent.WithSeal(header)
		rawdb.WriteBlock(db, block)
		rawdb.WriteTd(db, block.Hash(), block.NumberU64(), big.NewInt(1))
		rawdb.WriteCanonicalHash(db, block.Hash(), block.NumberU64())
		rawdb.WriteHeadBlockHash(db, block.Hash())
		rawdb.WriteHeadHeaderHash(db, block.Hash())
		rawdb.WriteHeadFastBlockHash(db, block.Hash())
		profile.Anchor.Hash = block.Hash()
	case "genesis_head":
		rawdb.WriteHeadBlockHash(db, genesis.Hash())
		rawdb.WriteHeadHeaderHash(db, genesis.Hash())
		rawdb.WriteHeadFastBlockHash(db, genesis.Hash())
	case "wrong_anchor":
		profile.Anchor.Hash = common.HexToHash("0x01")
	case "invalid_anchor_identity":
		profile.Anchor.ChainID = 1
	case "missing_canonical_head":
		rawdb.DeleteCanonicalHash(db, f.parent.NumberU64())
	case "valid", "fast_sync":
	default:
		t.Fatal("unknown fixture case", mode)
	}
	requireNoError(t, db.Close())
	blob, err := json.MarshalIndent(profile, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(directory, "profile.json"), blob, 0600))
}
