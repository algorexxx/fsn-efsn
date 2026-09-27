package eth

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/eth/downloader"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/event"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type retryAdmission struct {
	Head      common.Hash
	Height    uint64
	Hash      common.Hash
	Bytes     hexutil.Bytes
	PeerKnown bool
	Error     string
}

type retryPoolRecorder struct {
	*core.TxPool
	chain   *core.BlockChain
	peer    *peer
	mu      sync.Mutex
	records []retryAdmission
}

func (p *retryPoolRecorder) AddRemotes(txs []*types.Transaction) []error {
	head := p.chain.CurrentBlock()
	known := make([]bool, len(txs))
	for i, tx := range txs {
		known[i] = p.peer.knownTxs.Contains(tx.Hash())
	}
	errs := p.TxPool.AddRemotes(txs)
	p.mu.Lock()
	defer p.mu.Unlock()
	for i, tx := range txs {
		encoded, _ := tx.MarshalBinary()
		record := retryAdmission{Head: head.Hash(), Height: head.NumberU64(), Hash: tx.Hash(), Bytes: encoded, PeerKnown: known[i]}
		if errs[i] != nil {
			record.Error = errs[i].Error()
		}
		p.records = append(p.records, record)
	}
	return errs
}

func (p *retryPoolRecorder) observations() []retryAdmission {
	p.mu.Lock()
	defer p.mu.Unlock()
	return append([]retryAdmission(nil), p.records...)
}

type retryHistoricalChain struct {
	*core.BlockChain
	head *types.Block
}

func (c retryHistoricalChain) CurrentBlock() *types.Block { return c.head }

type retryWire struct {
	*p2p.MsgPipeRW
	writes atomic.Uint64
}

func (w *retryWire) WriteMsg(msg p2p.Msg) error {
	w.writes.Add(1)
	return w.MsgPipeRW.WriteMsg(msg)
}

type retryConnection struct {
	sender   *peer
	receiver *peer
	wire     *retryWire
	closed   bool
}

func openRetryConnection(t *testing.T, sender *ProtocolManager, receiver *retryPoolRecorder) *retryConnection {
	t.Helper()
	left, right := p2p.MsgPipe()
	wire := &retryWire{MsgPipeRW: left}
	connection := &retryConnection{
		sender:   newPeer(eth63, p2p.NewPeer(discover.NodeID{2}, "receiver", nil), wire),
		receiver: newPeer(eth63, p2p.NewPeer(discover.NodeID{1}, "sender", nil), right),
		wire:     wire,
	}
	connection.receiver.td = new(big.Int)
	receiver.peer = connection.receiver
	retryRequire(t, sender.peers.Register(connection.sender))
	t.Cleanup(func() { connection.close(t, sender) })
	return connection
}

func (c *retryConnection) close(t *testing.T, sender *ProtocolManager) {
	t.Helper()
	if c.closed {
		return
	}
	c.closed = true
	retryRequire(t, c.wire.Close())
	retryRequire(t, sender.peers.Unregister(c.sender.id))
}

func deliverRetryMessage(t *testing.T, receiver *ProtocolManager, connection *retryConnection, send func() error) {
	t.Helper()
	done := make(chan error, 2)
	go func() { done <- receiver.handleMsg(connection.receiver) }()
	go func() { done <- send() }()
	for i := 0; i < 2; i++ {
		select {
		case err := <-done:
			retryRequire(t, err)
		case <-time.After(10 * time.Second):
			t.Fatal("peer message did not complete")
		}
	}
}

func requireRetrySuppressed(t *testing.T, sender *ProtocolManager, connection *retryConnection, tx *types.Transaction) {
	t.Helper()
	before := connection.wire.writes.Load()
	if len(sender.peers.PeersWithoutTx(tx.Hash())) != 0 {
		t.Fatal("peer lost its known-transaction entry")
	}
	sender.BroadcastTxs(types.Transactions{tx})
	if connection.wire.writes.Load() != before || len(connection.sender.queuedTxs) != 0 {
		t.Fatal("known-peer ordinary broadcast unexpectedly sent or queued a message")
	}
}

func TestRestartPeerPurchaseRetry(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_PEER_RETRY")
	if root == "" {
		t.Skip("requires a fresh verified disposable copy and an isolated network namespace")
	}
	if !filepath.IsAbs(root) || filepath.Base(root) != "peer-purchase-retry-2026-09-27" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("explicit disposable peer-retry root and no original backup required")
	}
	interfaces, err := net.Interfaces()
	retryRequire(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 {
		t.Fatal("private loopback-only network namespace required")
	}
	var proof struct {
		Files int
		Bytes int64
	}
	retryReadJSON(t, filepath.Join(root, "receiver", "peer-retry-copy.json"), &proof)
	if proof.Files != 304 || proof.Bytes != 573895030 {
		t.Fatal("unexpected disposable copy manifest")
	}
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlDebug, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	datong.InitCheckPoints("")
	var saved struct {
		Header *types.Header
		Saved  hexutil.Bytes
	}
	retryReadJSON(t, "../docs/evidence/restart-existing-funds-2026-09-27/diagnostic-saved-producer.json", &saved)
	var tx types.Transaction
	retryRequire(t, tx.UnmarshalBinary(saved.Saved))
	if tx.Hash() != common.HexToHash("0xdfea27eab0a6b3cd87782ff072176c2daa98222c9e764fdcf30c0fc75f30737f") {
		t.Fatal("unexpected retained purchase")
	}
	encoded, err := os.ReadFile("../docs/evidence/restart-existing-funds-2026-09-27/blocks/block-19.rlp")
	retryRequire(t, err)
	var block *types.Block
	retryRequire(t, rlp.DecodeBytes(encoded, &block))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(root, "receiver", "chaindata"), 128, 64, "peer-retry", false)
	retryRequire(t, err)
	defer db.Close()
	config := rawdb.ReadChainConfig(db, rawdb.ReadCanonicalHash(db, 0))
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	retryRequire(t, err)
	defer chain.Stop()
	if chain.CurrentBlock().Hash() != saved.Header.Hash() || block.NumberU64() != 15130099 {
		t.Fatal("copy or retained block differs from the failed run")
	}
	for _, mode := range []string{"same-peer-resend", "ready-reconnect", "early-reconnect", "automatic-rebroadcast"} {
		if !t.Run(mode, func(t *testing.T) {
			retryRequire(t, chain.SetHead(block.NumberU64()-1))
			if chain.CurrentBlock().Hash() != block.ParentHash() {
				t.Fatal("disposable rewind did not reach the specified parent")
			}
			retryRequire(t, chain.CheckRestartReady())
			rehearseRetryMessages(t, root, mode, chain, db, engine, block, &tx, saved.Saved)
		}) {
			t.Fatal("peer retry case failed; retaining its state")
		}
	}
	actual, err := rlp.EncodeToBytes(chain.CurrentBlock())
	retryRequire(t, err)
	if !bytes.Equal(actual, encoded) {
		t.Fatal("peer-imported block differs from the retained original")
	}
	t.Logf("four ordered peer cases passed with original purchase %s and original block %d %s; no signing or funding", tx.Hash().Hex(), block.NumberU64(), block.Hash().Hex())
}

func retryRequire(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func retryReadJSON(t *testing.T, path string, target interface{}) {
	t.Helper()
	data, err := os.ReadFile(path)
	retryRequire(t, err)
	retryRequire(t, json.Unmarshal(data, target))
}

func rehearseRetryMessages(t *testing.T, root, mode string, chain *core.BlockChain, db ethdb.Database, engine *datong.DaTong, block *types.Block, tx *types.Transaction, saved []byte) {
	t.Helper()
	config := core.DefaultTxPoolConfig
	config.Journal = ""
	recipient := &retryPoolRecorder{TxPool: core.NewTxPool(config, chain.Config(), chain), chain: chain}
	t.Cleanup(recipient.Stop)
	origin := core.NewTxPool(config, chain.Config(), retryHistoricalChain{chain, block})
	t.Cleanup(origin.Stop)
	retryRequire(t, origin.AddLocal(tx))
	sender := &ProtocolManager{txpool: origin, peers: newPeerSet(), txsyncCh: make(chan *txsync), quitSync: make(chan struct{})}
	api := &EthAPIBackend{eth: &Ethereum{blockchain: chain, txPool: origin, protocolManager: sender}}
	syncDone := make(chan struct{})
	go func() { sender.txsyncLoop(); close(syncDone) }()
	t.Cleanup(func() {
		close(sender.quitSync)
		select {
		case <-syncDone:
		case <-time.After(5 * time.Second):
			t.Error("transaction-sync loop did not stop")
		}
	})
	receiver, err := NewProtocolManager(chain.Config(), downloader.FullSync, 32659, new(event.TypeMux), recipient, engine, chain, db, 16)
	retryRequire(t, err)
	receiver.fetcher.Start()
	t.Cleanup(func() { receiver.fetcher.Stop(); receiver.downloader.Terminate() })
	atomic.StoreUint32(&receiver.acceptTxs, 1)
	connection := openRetryConnection(t, sender, recipient)
	trace, err := os.OpenFile(filepath.Join(root, mode+".jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	retryRequire(t, err)
	defer trace.Close()
	observe := func(stage string) {
		entry := map[string]interface{}{"Stage": stage, "Head": chain.CurrentBlock().Header(), "AcceptTxs": atomic.LoadUint32(&receiver.acceptTxs), "SenderKnown": connection.sender.knownTxs.Contains(tx.Hash()), "ReceiverKnown": connection.receiver.knownTxs.Contains(tx.Hash()), "ConnectionWrites": connection.wire.writes.Load(), "SenderStatus": origin.Status([]common.Hash{tx.Hash()})[0], "ReceiverStatus": recipient.Status([]common.Hash{tx.Hash()})[0], "Admissions": recipient.observations()}
		retryRequire(t, json.NewEncoder(trace).Encode(entry))
	}
	observe("before-send")
	deliverRetryMessage(t, receiver, connection, func() error { sender.BroadcastTxs(types.Transactions{tx}); return nil })
	requireRetryRejections(t, recipient, tx, saved, 1)
	observe("rejected-before-block")
	if err := origin.AddLocal(tx); err != core.ErrAlreadyKnown {
		t.Fatalf("duplicate local submission: got %v, want already known", err)
	}
	requireRetrySuppressed(t, sender, connection, tx)
	observe("local-resubmit-and-ordinary-broadcast-suppressed")
	resend := func() error {
		if mode == "automatic-rebroadcast" {
			return api.RebroadcastTx(context.Background(), tx)
		}
		return connection.sender.SendTransactions([]*types.Transaction{tx})
	}
	deliverRetryMessage(t, receiver, connection, resend)
	requireRetryRejections(t, recipient, tx, saved, 2)
	observe("explicit-retry-still-rejected-before-block")
	parent := chain.CurrentBlock()
	td := new(big.Int).Add(chain.GetTd(parent.Hash(), parent.NumberU64()), block.Difficulty())
	deliverRetryMessage(t, receiver, connection, func() error { return connection.sender.SendNewBlock(block, td) })
	entrant := common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")
	retryAwait(t, func() bool { return chain.CurrentBlock().Hash() == block.Hash() && recipient.Nonce(entrant) == 14 })
	if recipient.Get(tx.Hash()) != nil || len(recipient.observations()) != 2 {
		t.Fatal("block import unexpectedly retained or readmitted a rejected purchase")
	}
	requireRetrySuppressed(t, sender, connection, tx)
	observe("block-imported-ordinary-broadcast-still-suppressed")
	if mode == "same-peer-resend" || mode == "automatic-rebroadcast" {
		deliverRetryMessage(t, receiver, connection, resend)
	} else {
		connection.close(t, sender)
		connection = openRetryConnection(t, sender, recipient)
		if mode == "early-reconnect" {
			atomic.StoreUint32(&receiver.acceptTxs, 0)
		}
		observe("new-connection-before-pending-replay")
		deliverRetryMessage(t, receiver, connection, func() error { sender.syncTransactions(connection.sender); return nil })
		if mode == "early-reconnect" {
			if len(recipient.observations()) != 2 || recipient.Get(tx.Hash()) != nil || connection.receiver.knownTxs.Contains(tx.Hash()) || !connection.sender.knownTxs.Contains(tx.Hash()) {
				t.Fatal("readiness-gated reconnect did not discard before remote admission")
			}
			observe("reconnect-replay-discarded-before-readiness")
			atomic.StoreUint32(&receiver.acceptTxs, 1)
			requireRetrySuppressed(t, sender, connection, tx)
			observe("readiness-enabled-ordinary-broadcast-still-suppressed")
			connection.close(t, sender)
			connection = openRetryConnection(t, sender, recipient)
			deliverRetryMessage(t, receiver, connection, func() error { sender.syncTransactions(connection.sender); return nil })
		}
	}
	retryAwait(t, func() bool { return recipient.Status([]common.Hash{tx.Hash()})[0] == core.TxStatusPending })
	records := recipient.observations()
	if len(records) != 3 || records[2].Error != "" || !records[2].PeerKnown || records[2].Head != block.Hash() || !bytes.Equal(records[2].Bytes, saved) {
		t.Fatalf("final peer admission differs: %+v", records)
	}
	owner, err := types.Sender(types.LatestSigner(chain.Config()), tx)
	retryRequire(t, err)
	state, err := chain.State()
	retryRequire(t, err)
	if state.GetNonce(owner) != 8 || recipient.Nonce(owner) != 9 {
		t.Fatal("canonical or pending nonce differs after readmission")
	}
	observe("exact-purchase-admitted-after-readiness")
	t.Logf("mode=%s exact transaction %s rejected twice before original block, ordinary rebroadcast suppressed, then admitted remotely without replacement; receiver canonical nonce=8 pending nonce=9", mode, tx.Hash().Hex())
}

func requireRetryRejections(t *testing.T, pool *retryPoolRecorder, tx *types.Transaction, saved []byte, count int) {
	t.Helper()
	records := pool.observations()
	if len(records) != count || pool.Get(tx.Hash()) != nil {
		t.Fatal("expected rejected purchase absent from the remote pool")
	}
	for _, record := range records {
		if record.Height != 15130098 || record.Error != "BuyTicket start must be lower than latest block time + 3 hour" || !record.PeerKnown || record.Hash != tx.Hash() || !bytes.Equal(record.Bytes, saved) {
			t.Fatal(fmt.Sprintf("unexpected remote admission: %+v", record))
		}
	}
}

func retryAwait(t *testing.T, ready func() bool) {
	t.Helper()
	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		if ready() {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatal("peer import or pool transition timed out")
}
