package restart

import (
	"encoding/json"
	"math/big"
	"net/url"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/eth"
	"github.com/FusionFoundation/efsn/v5/eth/downloader"
	"github.com/FusionFoundation/efsn/v5/eth/ethconfig"
	"github.com/FusionFoundation/efsn/v5/ethstats"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestDashboardTelemetryNode(t *testing.T) {
	path := os.Getenv("FUSION_DASHBOARD_FIXTURE")
	if path == "" {
		t.Skip("requires an explicit synthetic loopback dashboard fixture")
	}
	var settings struct {
		Collector            string
		Secret               string
		TransactionsPerBlock int
	}
	data, err := os.ReadFile(filepath.Join(path, "settings.json"))
	requireNoError(t, err)
	requireNoError(t, json.Unmarshal(data, &settings))
	endpoint, err := url.Parse(settings.Collector)
	requireNoError(t, err)
	if !filepath.IsAbs(path) || (endpoint.Scheme != "ws" && endpoint.Scheme != "wss") || endpoint.Hostname() != "127.0.0.1" || endpoint.Port() == "" || endpoint.Path != "" || endpoint.User != nil || endpoint.RawQuery != "" || endpoint.Fragment != "" || len(settings.Secret) < 32 || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute fixture path, loopback collector, synthetic credential and no backup input required")
	}
	if settings.TransactionsPerBlock != 1 && settings.TransactionsPerBlock != 10 {
		t.Fatal("the fixture supports only one or ten transactions per block")
	}
	previous := common.UseDevnetRule
	common.UseDevnetRule = true
	datong.InitCheckPoints("")
	t.Cleanup(func() { common.UseDevnetRule = previous; datong.InitCheckPoints("") })
	keyBytes := make([]byte, 32)
	keyBytes[31] = 1
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	chainConfig := *params.DevnetChainConfig
	chainConfig.ConstantinopleBlock, chainConfig.PetersburgBlock, chainConfig.IstanbulBlock = common.Big0, common.Big0, common.Big0
	chainConfig.BerlinBlock, chainConfig.LondonBlock, chainConfig.EcoBlock = common.Big0, common.Big0, common.Big0
	genesis := &core.Genesis{Config: &chainConfig, GasLimit: 15000000, Difficulty: big.NewInt(1), Timestamp: 1700000000, Alloc: core.GenesisAlloc{owner: {Balance: decimal(t, "1000000000000000000000000")}}}
	genesis.TicketCreateInfo = &core.TicketsCreate{Owner: owner, Count: 2, Time: genesis.Timestamp}
	stack, err := node.New(&node.Config{
		Name: "dashboard-fixture", HTTPHost: "127.0.0.1", HTTPModules: []string{"eth", "fsn", "net", "txpool"},
		P2P: p2p.Config{NoDiscovery: true, NoDial: true},
	})
	requireNoError(t, err)
	t.Cleanup(func() { requireNoError(t, stack.Close()) })
	config := ethconfig.Defaults
	config.Genesis, config.NetworkId, config.SyncMode = genesis, 99032659, downloader.FullSync
	config.NoPruning = true
	config.DatabaseCache, config.DatabaseHandles = 16, 16
	config.TrieCleanCache, config.TrieDirtyCache = 16, 0
	config.LightPeers = 0
	config.TxPool.Journal = ""
	service, err := eth.New(stack, &config)
	requireNoError(t, err)
	service.SetEtherbase(owner)
	f := &fixture{db: service.ChainDb(), chain: service.BlockChain(), engine: service.Engine().(*datong.DaTong), key: key, owner: owner}
	for number := 1; number <= 60; number++ {
		parent := f.chain.CurrentBlock()
		purchase := f.signPurchase(t, parent.Time(), common.TimeLockForever)
		txs := []*types.Transaction{purchase}
		for offset := 1; offset < settings.TransactionsPerBlock; offset++ {
			tx, err := types.SignTx(types.NewTransaction(purchase.Nonce()+uint64(offset), owner, new(big.Int), 21000, purchase.GasPrice(), nil), types.LatestSigner(f.chain.Config()), key)
			requireNoError(t, err)
			txs = append(txs, tx)
		}
		f.importBlock(t, f.buildBlockWithTransactions(t, parent.Time()+120, txs))
	}
	requireNoError(t, ethstats.New(stack, service.APIBackend, service.Engine(), "node-a:"+settings.Secret+"@"+settings.Collector))
	requireNoError(t, stack.Start())
	ready, err := json.Marshal(map[string]interface{}{"rpc": stack.HTTPEndpoint(), "owner": owner, "head": f.chain.CurrentBlock().Hash(), "height": 60})
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "ready.json"), ready, 0600))
	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Stat(filepath.Join(path, "stop")); err == nil {
			if service.IsMining() || stack.Server().PeerCount() != 0 || f.chain.CurrentBlock().NumberU64() != 60 {
				t.Fatal("stationary fixture changed unexpectedly")
			}
			return
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatal("dashboard fixture controller did not stop the node")
}
