package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func writePruningJSON(t *testing.T, path string, value interface{}) {
	t.Helper()
	blob, err := json.MarshalIndent(value, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(path, blob, 0600))
}

func pruningHeader(block *types.Block) map[string]interface{} {
	return map[string]interface{}{"head": block.NumberU64(), "hash": block.Hash(), "root": block.Root(), "tickets": block.MixDigest()}
}

func TestPreparePruningStartup(t *testing.T) {
	directory := os.Getenv("FUSION_STARTUP_TEST_DIRECTORY")
	if directory == "" {
		t.Skip("requires a new synthetic fixture directory")
	}
	if _, err := os.Stat(directory); !os.IsNotExist(err) {
		t.Fatal("fixture must not exist")
	}
	keyBytes := make([]byte, 32)
	keyBytes[31] = 1
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	config := *params.MainnetChainConfig
	config.ConstantinopleBlock, config.PetersburgBlock, config.IstanbulBlock = common.Big0, common.Big0, common.Big0
	config.BerlinBlock, config.LondonBlock, config.EcoBlock = common.Big0, common.Big0, common.Big0
	genesis := &core.Genesis{Config: &config, GasLimit: 15000000, Difficulty: big.NewInt(1), Timestamp: 1700000000, TicketCreateInfo: &core.TicketsCreate{Owner: owner, Count: 132, Time: 1700000000}, Alloc: core.GenesisAlloc{owner: {Balance: decimal(t, "1000000000000000000000000")}}}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "efsn", "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	defer db.Close()
	base := genesis.MustCommit(db)
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	defer chain.Stop()
	f := &fixture{db: db, chain: chain, engine: engine, key: key, owner: owner, parent: base}
	for number := 1; number <= 129; number++ {
		f.importBlock(t, f.buildBlock(t, chain.CurrentBlock().Time()+120, false))
	}
	parent := chain.CurrentBlock()
	for number := uint64(0); number <= 129; number++ {
		block := chain.GetBlockByNumber(number)
		if block == nil || block.NumberU64() != number {
			t.Fatalf("missing ancestor %d", number)
		}
		if number > 0 && block.ParentHash() != chain.GetBlockByNumber(number-1).Hash() {
			t.Fatalf("broken ancestry %d", number)
		}
	}
	child := f.buildBlock(t, parent.Time()+120, false)
	encoded, err := rlp.EncodeToBytes(child)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(directory, "child.rlp"), encoded, 0600))
	writePruningJSON(t, filepath.Join(directory, "expected.json"), map[string]interface{}{"parent": pruningHeader(parent), "child": pruningHeader(child), "ancestor_count": 130})
	profile := struct {
		Genesis common.Hash
		Config  *params.ChainConfig
		Anchor  *params.RestartAnchor
	}{base.Hash(), &config, &params.RestartAnchor{GenesisHash: base.Hash(), ChainID: 32659, Number: 129, Hash: parent.Hash()}}
	writePruningJSON(t, filepath.Join(directory, "profile.json"), profile)
	t.Logf("complete synthetic ancestry 0..129; child=%s; public key 1; no real keys", child.Hash())
}

func TestInspectPruningStartup(t *testing.T) {
	directory := os.Getenv("FUSION_STARTUP_TEST_DIRECTORY")
	if directory == "" {
		t.Skip("requires a closed synthetic fixture")
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "efsn", "chaindata"), 16, 16, "", true)
	requireNoError(t, err)
	defer db.Close()
	head := rawdb.ReadHeadBlockHash(db)
	number := rawdb.ReadHeaderNumber(db, head)
	if number == nil || *number != 130 {
		t.Fatal("expected head 130")
	}
	var observations []map[string]interface{}
	for _, height := range []uint64{130, 129, 3} {
		hash := rawdb.ReadCanonicalHash(db, height)
		block := rawdb.ReadBlock(db, hash, height)
		if block == nil {
			t.Fatalf("missing block %d", height)
		}
		statedb, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db))
		requireNoError(t, err)
		tickets, err := statedb.AllTickets()
		requireNoError(t, err)
		requireNoError(t, state.AddCachedTickets(block.MixDigest(), tickets))
		if crypto.Keccak256Hash(statedb.GetData(common.TicketKeyAddress)) != block.MixDigest() {
			t.Fatal("ticket commitment differs")
		}
		requireNoError(t, statedb.Error())
		observations = append(observations, pruningHeader(block))
	}
	blob, err := json.Marshal(observations)
	requireNoError(t, err)
	t.Logf("PRUNINGCOLD %s", blob)
}
