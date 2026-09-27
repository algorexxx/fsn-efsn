package restart

import (
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/accounts/keystore"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/eth"
	"github.com/FusionFoundation/efsn/v5/eth/downloader"
	"github.com/FusionFoundation/efsn/v5/eth/ethconfig"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type nodeRehearsalConfig struct {
	Anchor         *params.RestartAnchor
	GasLimit       uint64
	MainnetGenesis bool
	DenseGenesis   *core.Genesis
	TestKey        byte
	AutoBuy        bool
	ListenAddr     string
}

type nodeRehearsalStatus struct {
	Number     uint64
	Hash       common.Hash
	Root       common.Hash
	Tickets    common.Hash
	Full       common.Hash
	Header     common.Hash
	Fast       common.Hash
	TD         *hexutil.Big
	Signatures uint64
	Pending    int
	Queued     int
	AutoBuy    bool
	Mining     bool
}

type nodeRehearsalAPI struct {
	service    *eth.Ethereum
	signatures atomic.Uint64
	testKey    byte
}

func (a *nodeRehearsalAPI) Status() nodeRehearsalStatus {
	chain := a.service.BlockChain()
	head := chain.CurrentBlock()
	db := a.service.ChainDb()
	pending, queued := a.service.TxPool().Stats()
	return nodeRehearsalStatus{
		Number: head.NumberU64(), Hash: head.Hash(), Root: head.Root(), Tickets: head.MixDigest(),
		Full: rawdb.ReadHeadBlockHash(db), Header: rawdb.ReadHeadHeaderHash(db), Fast: rawdb.ReadHeadFastBlockHash(db),
		TD: (*hexutil.Big)(chain.GetTd(head.Hash(), head.NumberU64())), Signatures: a.signatures.Load(), Pending: pending, Queued: queued,
		AutoBuy: common.IsAutoBuyTicketEnabled(), Mining: a.service.IsMining(),
	}
}

func (a *nodeRehearsalAPI) Construct(plan recovery.Plan, purchase hexutil.Bytes) (common.Hash, error) {
	if a.service.IsMining() {
		return common.Hash{}, fmt.Errorf("stop ordinary mining before controlled construction")
	}
	var tx types.Transaction
	if err := rlp.DecodeBytes(purchase, &tx); err != nil {
		return common.Hash{}, err
	}
	keyBytes := make([]byte, 32)
	keyBytes[31] = a.testKey
	key, err := crypto.ToECDSA(keyBytes)
	if err != nil {
		return common.Hash{}, err
	}
	owner := crypto.PubkeyToAddress(key.PublicKey)
	if owner != plan.Signer {
		return common.Hash{}, fmt.Errorf("plan signer differs from this public test key")
	}
	chain := a.service.BlockChain()
	candidate, err := recovery.Build(chain, plan, types.Transactions{&tx})
	if err != nil {
		return common.Hash{}, err
	}
	engine := a.service.Engine().(*datong.DaTong)
	engine.Authorize(owner, func(_ accounts.Account, _ string, data []byte) ([]byte, error) {
		a.signatures.Add(1)
		return crypto.Sign(crypto.Keccak256(data), key)
	})
	results := make(chan *types.Block, 1)
	stop := make(chan struct{})
	defer close(stop)
	if err := engine.Seal(chain, candidate.Block, results, stop); err != nil {
		return common.Hash{}, err
	}
	select {
	case block := <-results:
		_, err := chain.InsertChain(types.Blocks{block})
		if err == nil {
			a.service.EventMux().Post(core.NewMinedBlockEvent{Block: block})
		}
		return block.Hash(), err
	case <-time.After(5 * time.Second):
		return common.Hash{}, fmt.Errorf("historical construction did not seal")
	}
}

func (a *nodeRehearsalAPI) Sync(id string, hash common.Hash, td *hexutil.Big) error {
	return a.service.Downloader().Synchronise(id, hash, (*big.Int)(td), downloader.FullSync)
}

func (a *nodeRehearsalAPI) StartWorker() error {
	keyBytes := make([]byte, 32)
	keyBytes[31] = 1
	key, err := crypto.ToECDSA(keyBytes)
	if err != nil {
		return err
	}
	owner := crypto.PubkeyToAddress(key.PublicKey)
	a.service.Engine().(*datong.DaTong).Authorize(owner, func(_ accounts.Account, _ string, data []byte) ([]byte, error) {
		a.signatures.Add(1)
		return crypto.Sign(crypto.Keccak256(data), key)
	})
	a.service.Miner().Start(owner)
	return nil
}

func (a *nodeRehearsalAPI) Block(number uint64) (hexutil.Bytes, error) {
	block := a.service.BlockChain().GetBlockByNumber(number)
	if block == nil {
		return nil, fmt.Errorf("missing block %d", number)
	}
	return rlp.EncodeToBytes(block)
}

func (a *nodeRehearsalAPI) BlockByHash(hash common.Hash) (hexutil.Bytes, error) {
	block := a.service.BlockChain().GetBlockByHash(hash)
	if block == nil {
		return nil, fmt.Errorf("missing block %s", hash)
	}
	return rlp.EncodeToBytes(block)
}

func TestRestartNodeRehearsal(t *testing.T) {
	if os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" {
		t.Skip("opt-in Linux service rehearsal requires an isolated loopback-only network namespace")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("rehearsal requires exactly one interface: an enabled loopback in a private network namespace")
	}
	if path := os.Getenv("FUSION_RESTART_LAB_NODE"); path != "" {
		runRehearsalNode(t, path)
		return
	}
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	datong.InitCheckPoints("")
	t.Run("readiness_mining_crash", rehearseNodeReadiness)
	t.Run("compatible_peer", rehearseCompatiblePeer)
	t.Run("purchase_peer_reinclusion", func(t *testing.T) { rehearsePurchasePeer(t, false) })
	t.Run("purchase_peer_replacement", func(t *testing.T) { rehearsePurchasePeer(t, true) })
	t.Run("purchase_peer_nonce_rollback", rehearsePurchaseNonceRollback)
	t.Run("competing_purchase_miners", rehearseCompetingPurchaseMiners)
	t.Run("partition_purchase_miners", rehearsePartitionPurchaseMiners)
	t.Run("dense_miner_fixture", rehearseDenseMinerFixture)
	t.Run("continuous_partition_miners", rehearseContinuousPartitionMiners)
	t.Run("continuous_partition_nonce_repair", rehearseContinuousPartitionNonceRepair)
	t.Run("small_reserve_nonce_repair", rehearseSmallReserveNonceRepair)
	t.Run("funded_small_reserve_repair", rehearseFundedSmallReserveRepair)
	t.Run("controlled_zero_ticket_reserves", rehearseControlledZeroTicketReserves)
	t.Run("heavier_stored_fork_peer", rehearseHeavierPeer)
	t.Run("incompatible_database_startup", rehearseIncompatibleStartup)
}

func runRehearsalNode(t *testing.T, path string) {
	level := log.LvlInfo
	if os.Getenv("FUSION_RESTART_NODE_DEBUG") == "1" {
		level = log.LvlDebug
	}
	log.Root().SetHandler(log.LvlFilterHandler(level, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	data, err := os.ReadFile(filepath.Join(path, "lab.json"))
	requireNoError(t, err)
	var lab nodeRehearsalConfig
	requireNoError(t, json.Unmarshal(data, &lab))
	if lab.DenseGenesis != nil {
		common.UseDevnetRule = true
		datong.InitCheckPoints("")
	}
	if lab.TestKey == 0 {
		lab.TestKey = 1
	}
	if lab.TestKey != 1 && lab.TestKey != 2 && lab.TestKey != 3 {
		t.Fatal("only public rehearsal keys 1, 2 and 3 are permitted")
	}
	if lab.ListenAddr == "" {
		lab.ListenAddr = "127.0.0.1:0"
	}
	restrict, err := netutil.ParseNetlist("127.0.0.0/8")
	requireNoError(t, err)
	stack, err := node.New(&node.Config{
		Name: "anchor-lab", DataDir: path, IPCPath: "lab.ipc", UseLightweightKDF: true,
		P2P: p2p.Config{MaxPeers: 4, NoDiscovery: true, ListenAddr: lab.ListenAddr, NetRestrict: restrict},
	})
	requireNoError(t, err)
	t.Cleanup(func() { stack.Close() })
	keys := keystore.NewKeyStore(filepath.Join(path, "keystore"), keystore.LightScryptN, keystore.LightScryptP)
	stack.AccountManager().AddBackend(keys)
	keyBytes := make([]byte, 32)
	keyBytes[31] = lab.TestKey
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	account := accounts.Account{Address: crypto.PubkeyToAddress(key.PublicKey)}
	if !keys.HasAddress(account.Address) {
		account, err = keys.ImportECDSA(key, "public-synthetic-key")
		requireNoError(t, err)
	}
	requireNoError(t, keys.Unlock(account, "public-synthetic-key"))
	chainConfig := *params.MainnetChainConfig
	chainConfig.RestartAnchor = lab.Anchor
	config := ethconfig.Defaults
	config.Genesis = &core.Genesis{Config: &chainConfig, GasLimit: lab.GasLimit, Difficulty: big.NewInt(1)}
	if lab.MainnetGenesis {
		config.Genesis = core.DefaultGenesisBlock()
		config.Genesis.Config = &chainConfig
	}
	if lab.DenseGenesis != nil {
		chainConfig = *lab.DenseGenesis.Config
		chainConfig.RestartAnchor = lab.Anchor
		config.Genesis = lab.DenseGenesis
		config.Genesis.Config = &chainConfig
	}
	config.NetworkId = 99032659
	config.SyncMode = downloader.FullSync
	config.NoPruning = true
	config.DatabaseCache, config.DatabaseHandles = 16, 16
	config.TrieCleanCache, config.TrieDirtyCache = 16, 0
	config.LightPeers = 0
	config.Miner.GasCeil, config.Miner.GasPrice, config.Miner.Recommit = lab.GasLimit, big.NewInt(1), time.Second
	config.TxPool.Journal = ""
	service, err := eth.New(stack, &config)
	requireNoError(t, err)
	service.SetEtherbase(account.Address)
	stack.RegisterAPIs([]rpc.API{{Namespace: "lab", Version: "1.0", Service: &nodeRehearsalAPI{service: service, testKey: lab.TestKey}}})
	stack.RegisterLifecycle(ethapi.NewTicketBuyer(lab.AutoBuy))
	datong.InitCheckPoints("")
	requireNoError(t, stack.Start())
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM)
	defer signal.Stop(stop)
	<-stop
}

type rehearsalNode struct {
	client *rpc.Client
	cmd    *exec.Cmd
	done   chan error
	path   string
}

func seedRehearsalNode(t *testing.T) (string, *fixture) {
	t.Helper()
	path, err := os.MkdirTemp("", "fsn-lab-")
	requireNoError(t, err)
	t.Cleanup(func() { os.RemoveAll(path) })
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "anchor-lab", "chaindata"), 16, 16, "", false)
	requireNoError(t, err)
	return path, newFixtureInDatabase(t, 0, db)
}

func closeRehearsalSeed(t *testing.T, path string, f *fixture, anchor *types.Block) {
	t.Helper()
	lab := nodeRehearsalConfig{GasLimit: f.chain.Genesis().GasLimit()}
	if anchor != nil {
		lab.Anchor = &params.RestartAnchor{GenesisHash: f.chain.Genesis().Hash(), ChainID: f.chain.Config().ChainID.Uint64(), Number: anchor.NumberU64(), Hash: anchor.Hash()}
	}
	data, err := json.MarshalIndent(lab, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "lab.json"), data, 0600))
	f.chain.Stop()
	requireNoError(t, f.db.Close())
}

func startRehearsalNode(t *testing.T, path string) *rehearsalNode {
	t.Helper()
	return startRehearsalNodeWithTimeout(t, path, 6*time.Minute)
}

func startRehearsalNodeWithTimeout(t *testing.T, path string, timeout time.Duration) *rehearsalNode {
	t.Helper()
	output, err := os.CreateTemp(path, "process-*.log")
	requireNoError(t, err)
	cmd := exec.Command(os.Args[0], "-test.run=^TestRestartNodeRehearsal$", "-test.v", "-test.timeout="+timeout.String())
	cmd.Env = append(os.Environ(), "FUSION_RESTART_LAB_NODE="+path)
	cmd.Stdout, cmd.Stderr = output, output
	requireNoError(t, cmd.Start())
	n := &rehearsalNode{cmd: cmd, done: make(chan error, 1), path: path}
	go func() { n.done <- cmd.Wait(); close(n.done) }()
	t.Cleanup(func() {
		n.stop(t, false)
		output.Close()
		data, err := os.ReadFile(output.Name())
		requireNoError(t, err)
		t.Logf("node process %s:\n%s", output.Name(), data)
		if strings.Contains(string(data), "WARNING: DATA RACE") {
			t.Error("node process reported a data race")
		}
	})
	awaitRehearsal(t, 60*time.Second, func() bool {
		select {
		case err := <-n.done:
			t.Fatalf("node exited before IPC: %v", err)
		default:
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		client, err := rpc.DialIPC(ctx, filepath.Join(path, "lab.ipc"))
		if err != nil {
			return false
		}
		n.client = client
		return true
	})
	return n
}

func (n *rehearsalNode) call(t *testing.T, result interface{}, method string, args ...interface{}) error {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
	defer cancel()
	return n.client.CallContext(ctx, result, method, args...)
}

func (n *rehearsalNode) status(t *testing.T) nodeRehearsalStatus {
	t.Helper()
	var status nodeRehearsalStatus
	requireNoError(t, n.call(t, &status, "lab_status"))
	return status
}

func (n *rehearsalNode) stop(t *testing.T, crash bool) {
	t.Helper()
	if n.cmd == nil {
		return
	}
	if n.client != nil {
		n.client.Close()
	}
	if crash {
		requireNoError(t, n.cmd.Process.Kill())
	} else {
		n.cmd.Process.Signal(syscall.SIGTERM)
	}
	select {
	case err := <-n.done:
		if !crash && err != nil {
			t.Errorf("node shutdown: %v", err)
		}
	case <-time.After(10 * time.Second):
		n.cmd.Process.Kill()
		<-n.done
		t.Error("node did not shut down within ten seconds")
	}
	n.cmd = nil
}

func awaitRehearsal(t *testing.T, timeout time.Duration, ready func() bool) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if ready() {
			return
		}
		time.Sleep(100 * time.Millisecond)
	}
	t.Fatal("node rehearsal condition timed out")
}

func requireRehearsalHead(t *testing.T, status nodeRehearsalStatus, block *types.Block) {
	t.Helper()
	if status.Hash != block.Hash() || status.Full != block.Hash() || status.Header != block.Hash() || status.Fast != block.Hash() || status.Number != block.NumberU64() || status.Root != block.Root() || status.Tickets != block.MixDigest() {
		t.Fatalf("node commitments differ from expected block %d %s: %+v", block.NumberU64(), block.Hash().Hex(), status)
	}
}

func rehearseNodeReadiness(t *testing.T) {
	path, receiver := seedRehearsalNode(t)
	producer := newFixture(t)
	advancePurchaseFixture(t, producer, receiver)
	shared := receiver.chain.CurrentBlock()
	belowTx, err := rlp.EncodeToBytes(receiver.signPurchase(t, shared.Time(), common.TimeLockForever))
	requireNoError(t, err)
	accepted := roundTripBlocks(t, buildAnchorBranch(t, producer, 4, 120))
	nextTx := producer.signPurchase(t, producer.chain.CurrentBlock().Time(), common.TimeLockForever)
	rawTx, err := rlp.EncodeToBytes(nextTx)
	requireNoError(t, err)
	closeRehearsalSeed(t, path, receiver, accepted[0])
	n := startRehearsalNode(t, path)
	var syncing json.RawMessage
	requireNoError(t, n.call(t, &syncing, "eth_syncing"))
	if string(syncing) == "false" {
		t.Fatal("RPC reported ready below the restart anchor")
	}
	requireErrorContains(t, n.call(t, nil, "miner_start", 1), "restart anchor")
	requireErrorContains(t, n.call(t, nil, "eth_sendRawTransaction", hexutil.Bytes(belowTx)), "restart anchor")
	status := n.status(t)
	requireRehearsalHead(t, status, shared)
	if status.Pending != 0 || status.Queued != 0 {
		t.Fatal("RPC admitted a transaction below the anchor")
	}
	requireNoError(t, n.call(t, nil, "lab_startWorker"))
	awaitRehearsal(t, 5*time.Second, func() bool {
		var mining bool
		requireNoError(t, n.call(t, &mining, "eth_mining"))
		return mining
	})
	time.Sleep(2 * time.Second)
	status = n.status(t)
	requireRehearsalHead(t, status, shared)
	if status.Signatures != 0 {
		t.Fatal("worker signed below the anchor")
	}
	requireNoError(t, n.call(t, nil, "miner_stop"))
	stream, err := os.Create(filepath.Join(path, "accepted.rlp"))
	requireNoError(t, err)
	for _, block := range accepted {
		requireNoError(t, rlp.Encode(stream, block))
	}
	requireNoError(t, stream.Close())
	var imported bool
	requireNoError(t, n.call(t, &imported, "admin_importChain", stream.Name()))
	if !imported {
		t.Fatal("RPC did not import the accepted bridge")
	}
	requireRehearsalHead(t, n.status(t), accepted[3])
	requireNoError(t, n.call(t, &syncing, "eth_syncing"))
	if string(syncing) != "false" {
		t.Fatalf("RPC did not report ready after the anchor: %s", syncing)
	}
	var txHash common.Hash
	requireNoError(t, n.call(t, &txHash, "eth_sendRawTransaction", hexutil.Bytes(rawTx)))
	if txHash != nextTx.Hash() {
		t.Fatal("RPC changed the submitted transaction")
	}
	requireNoError(t, n.call(t, nil, "miner_start", 1))
	awaitRehearsal(t, 25*time.Second, func() bool { return n.status(t).Number > accepted[3].NumberU64() })
	requireNoError(t, n.call(t, nil, "miner_stop"))
	mined := n.status(t)
	if mined.Number != accepted[3].NumberU64()+1 {
		t.Fatalf("unexpected mining advance: %d", mined.Number)
	}
	var encoded hexutil.Bytes
	requireNoError(t, n.call(t, &encoded, "lab_block", mined.Number))
	var block types.Block
	requireNoError(t, rlp.DecodeBytes(encoded, &block))
	verifyMinedPurchase(t, producer, &block, nextTx.Hash(), mined.Number)
	requireRehearsalHead(t, mined, &block)
	n.stop(t, true)
	reopened := startRehearsalNode(t, path)
	requireRehearsalHead(t, reopened.status(t), &block)
	var receipt *types.Receipt
	requireNoError(t, reopened.call(t, &receipt, "eth_getTransactionReceipt", nextTx.Hash()))
	if receipt == nil || receipt.BlockHash != block.Hash() || receipt.Status != types.ReceiptStatusSuccessful {
		t.Fatalf("receipt lost after process kill: %+v", receipt)
	}
	t.Logf("blocked RPC/miner/worker below anchor; accepted RPC import and purchase; independently verified mined block %d %s; all heads, roots and receipt survived SIGKILL/reopen", block.NumberU64(), block.Hash().Hex())
}

func rehearseCompatiblePeer(t *testing.T) {
	sourcePath, source := seedRehearsalNode(t)
	receiverPath, receiver := seedRehearsalNode(t)
	advancePurchaseFixture(t, source, receiver)
	accepted := roundTripBlocks(t, buildAnchorBranch(t, source, 4, 120))
	closeRehearsalSeed(t, sourcePath, source, accepted[0])
	closeRehearsalSeed(t, receiverPath, receiver, accepted[0])
	remote := startRehearsalNode(t, sourcePath)
	local := startRehearsalNode(t, receiverPath)
	id := connectRehearsalPeer(t, local, remote)
	head := remote.status(t)
	requireNoError(t, local.call(t, nil, "lab_sync", id, head.Hash, head.TD))
	requireRehearsalHead(t, local.status(t), accepted[3])
	t.Logf("real devp2p full sync crossed anchor and adopted block %d %s with matching state/ticket roots", accepted[3].NumberU64(), accepted[3].Hash().Hex())
}

func connectRehearsalPeer(t *testing.T, local, remote *rehearsalNode) string {
	t.Helper()
	var info p2p.NodeInfo
	requireNoError(t, remote.call(t, &info, "admin_nodeInfo"))
	var added bool
	requireNoError(t, local.call(t, &added, "admin_addPeer", info.Enode))
	if !added {
		t.Fatal("could not add loopback peer")
	}
	awaitRehearsal(t, 45*time.Second, func() bool {
		var peers []*p2p.PeerInfo
		requireNoError(t, local.call(t, &peers, "admin_peers"))
		for _, peer := range peers {
			if peer.ID == info.ID && peer.Protocols["efsn"] != nil && peer.Protocols["efsn"] != "handshake" {
				return true
			}
		}
		return false
	})
	return strings.TrimPrefix(info.ID, "0x")[:16]
}

func rehearseHeavierPeer(t *testing.T) {
	localPath, localSeed := seedRehearsalNode(t)
	remotePath, remoteSeed := seedRehearsalNode(t)
	advancePurchaseFixture(t, localSeed, remoteSeed)
	accepted := roundTripBlocks(t, buildAnchorBranch(t, localSeed, 4, 120))
	foreign := roundTripBlocks(t, buildAnchorBranch(t, remoteSeed, 5, 121))
	_, err := localSeed.chain.InsertChain(foreign[:2])
	requireNoError(t, err)
	if localSeed.chain.CurrentBlock().Hash() != accepted[3].Hash() {
		t.Fatal("stored side branch changed the initial canonical chain")
	}
	closeRehearsalSeed(t, localPath, localSeed, accepted[0])
	closeRehearsalSeed(t, remotePath, remoteSeed, nil)
	local := startRehearsalNode(t, localPath)
	remote := startRehearsalNode(t, remotePath)
	id := connectRehearsalPeer(t, local, remote)
	head := remote.status(t)
	before := local.status(t)
	if (*big.Int)(head.TD).Cmp((*big.Int)(before.TD)) <= 0 {
		t.Fatal("returning peer is not heavier")
	}
	err = local.call(t, nil, "lab_sync", id, head.Hash, head.TD)
	requireErrorContains(t, err, "restart anchor")
	requireErrorContains(t, err, foreign[0].Hash().Hex())
	requireErrorContains(t, err, accepted[0].Hash().Hex())
	requireRehearsalHead(t, local.status(t), accepted[3])
	var receipt *types.Receipt
	requireNoError(t, local.call(t, &receipt, "eth_getTransactionReceipt", accepted[3].Transactions()[0].Hash()))
	if receipt == nil || receipt.BlockHash != accepted[3].Hash() {
		t.Fatal("rejected peer changed accepted transaction lookup")
	}
	local.stop(t, false)
	reopened := startRehearsalNode(t, localPath)
	requireRehearsalHead(t, reopened.status(t), accepted[3])
	t.Logf("heavier peer rejected via real downloader from stored side ancestry: %v; canonical head and accepted receipt retained, clean reopen passed", err)
}

func rehearseIncompatibleStartup(t *testing.T) {
	path, returning := seedRehearsalNode(t)
	accepted := newFixture(t)
	advancePurchaseFixture(t, accepted, returning)
	anchor := buildAnchorBranch(t, accepted, 1, 120)[0]
	buildAnchorBranch(t, returning, 5, 121)
	returning.chain.Stop()
	before := databaseDigest(t, returning.db)
	closeRehearsalSeed(t, path, returning, anchor)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartNodeRehearsal$", "-test.v", "-test.timeout=15s")
	command.Env = append(os.Environ(), "FUSION_RESTART_LAB_NODE="+path)
	output, err := command.CombinedOutput()
	t.Logf("expected startup refusal:\n%s", output)
	if err == nil || !strings.Contains(string(output), "restart anchor: hash mismatch") || ctx.Err() != nil {
		t.Fatalf("expected incompatible startup refusal, got %v", err)
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "anchor-lab", "chaindata"), 16, 16, "", true)
	requireNoError(t, err)
	defer db.Close()
	if after := databaseDigest(t, db); after != before {
		t.Fatal("service startup rejection modified logical chain database contents")
	}
	t.Log("incompatible full-service startup refused; complete logical LevelDB digest unchanged")
}
