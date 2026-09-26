package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/params"
)

type denseMinerPair struct {
	paths   [2]string
	miners  [2]*fixture
	genesis *core.Genesis
}

func seedDenseMinerPair(t *testing.T) *denseMinerPair {
	t.Helper()
	previous := common.UseDevnetRule
	common.UseDevnetRule = true
	datong.InitCheckPoints("")
	t.Cleanup(func() { common.UseDevnetRule = previous; datong.InitCheckPoints("") })
	pair := &denseMinerPair{}
	config := *params.DevnetChainConfig
	config.ConstantinopleBlock, config.PetersburgBlock, config.IstanbulBlock = common.Big0, common.Big0, common.Big0
	config.BerlinBlock, config.LondonBlock, config.EcoBlock = common.Big0, common.Big0, common.Big0
	pair.genesis = &core.Genesis{Config: &config, GasLimit: 15000000, Difficulty: big.NewInt(1), Timestamp: uint64(time.Now().Unix()) - 3600, Alloc: make(core.GenesisAlloc)}
	for i := range pair.miners {
		keyBytes := make([]byte, 32)
		keyBytes[31] = byte(i + 1)
		key, err := crypto.ToECDSA(keyBytes)
		requireNoError(t, err)
		pair.miners[i] = &fixture{key: key, owner: crypto.PubkeyToAddress(key.PublicKey)}
		pair.genesis.Alloc[pair.miners[i].owner] = core.GenesisAccount{Balance: decimal(t, "1000000000000000000000000")}
	}
	pair.genesis.TicketCreateInfo = &core.TicketsCreate{Owner: pair.miners[0].owner, Count: 2, Time: pair.genesis.Timestamp}
	for i, f := range pair.miners {
		f := f
		path, err := os.MkdirTemp("", "fsn-dense-miner-")
		requireNoError(t, err)
		pair.paths[i] = path
		t.Cleanup(func() { os.RemoveAll(path) })
		f.db, err = rawdb.NewLevelDBDatabase(filepath.Join(path, "anchor-lab", "chaindata"), 16, 16, "", false)
		requireNoError(t, err)
		f.parent, err = pair.genesis.Commit(f.db)
		requireNoError(t, err)
		f.engine = datong.New(config.DaTong, f.db)
		f.chain, err = core.NewBlockChain(f.db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, f.engine, vm.Config{}, nil)
		requireNoError(t, err)
		t.Cleanup(func() { f.chain.Stop(); f.db.Close() })
	}
	for i := 0; i < 24; i++ {
		first, second := pair.miners[0], pair.miners[1]
		parent := first.chain.CurrentBlock()
		txs := []*types.Transaction{first.signPurchase(t, parent.Time(), common.TimeLockForever), second.signPurchase(t, parent.Time(), common.TimeLockForever)}
		producer := preferredFixtureProducer(t, first, second)
		block := producer.buildBlockWithTransactions(t, parent.Time()+120, txs)
		first.importBlock(t, block)
		second.importBlock(t, block)
	}
	return pair
}

func closeDenseMinerPair(t *testing.T, pair *denseMinerPair) {
	t.Helper()
	anchor := pair.miners[0].chain.CurrentBlock()
	for i, f := range pair.miners {
		closeTwoMinerSeed(t, pair.paths[i], f, anchor, byte(i+1))
		var config nodeRehearsalConfig
		path := filepath.Join(pair.paths[i], "lab.json")
		readHandoverJSON(t, path, &config)
		config.DenseGenesis = pair.genesis
		data, err := json.MarshalIndent(config, "", "  ")
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(path, data, 0600))
	}
}

func rehearseDenseMinerFixture(t *testing.T) {
	pair := seedDenseMinerPair(t)
	for number := uint64(0); number <= 24; number++ {
		first := pair.miners[0].chain.GetBlockByNumber(number)
		second := pair.miners[1].chain.GetBlockByNumber(number)
		if first == nil || second == nil || first.Hash() != second.Hash() {
			t.Fatalf("complete synthetic ancestry differs at %d", number)
		}
		if number > 0 && first.ParentHash() != pair.miners[0].chain.GetBlockByNumber(number-1).Hash() {
			t.Fatal("synthetic ancestry is not linked")
		}
	}
	anchor := pair.miners[0].chain.CurrentBlock()
	closeDenseMinerPair(t, pair)
	for _, path := range pair.paths {
		node := startRehearsalNode(t, path)
		requireRehearsalHead(t, node.status(t), anchor)
		if readPeerPurchase(t, node).Nonce != 24 {
			t.Fatal("cold synthetic owner must retain all twenty-four executed purchases")
		}
	}
	t.Logf("complete synthetic genesis-to-24 ancestry independently executed in two databases and accepted by both cold services; anchor=%s", anchor.Hash().Hex())
}
