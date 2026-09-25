package restart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/eth"
	"github.com/FusionFoundation/efsn/v5/eth/ethconfig"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type snapshotPeerStatus struct {
	Version uint32
	Network uint64
	TD      *big.Int
	Head    common.Hash
	Genesis common.Hash
}

func TestRestoredSnapshotService(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_RESTORED_NODE")
	if directory == "" {
		t.Skip("requires explicitly restored, checksum-verified disposable node directory")
	}
	if !filepath.IsAbs(directory) || filepath.Base(directory) != "efsn" {
		t.Fatal("absolute restored efsn instance directory required")
	}
	var marker struct {
		Manifest string `json:"manifest_sha256"`
		Files    uint64 `json:"files"`
		Bytes    uint64 `json:"bytes"`
	}
	data, err := os.ReadFile(filepath.Join(directory, "restored.json"))
	requireNoError(t, err)
	requireNoError(t, json.Unmarshal(data, &marker))
	if marker.Manifest == "" || marker.Manifest != os.Getenv("FUSION_RESTART_RESTORED_MANIFEST") || marker.Files != 56107 || marker.Bytes != 117170022674 {
		t.Fatal("restored marker differs from reviewed full backup package")
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 128, 128, "snapshot-preflight", true)
	requireNoError(t, err)
	reader, err := recovery.NewReader(db)
	if err != nil {
		db.Close()
		t.Fatal(err)
	}
	expected := reader.CurrentHeader()
	if expected.Hash() != common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f") {
		db.Close()
		t.Fatal("restored head mismatch")
	}
	requireNoError(t, db.Close())
	runRestoredSnapshotService(t, directory, expected)
	t.Log("restored full node startup/RPC/loopback-peer/clean-stop succeeded")
}

func runRestoredSnapshotService(t *testing.T, directory string, expected *types.Header) {
	t.Helper()
	restrict, err := netutil.ParseNetlist("127.0.0.0/8")
	requireNoError(t, err)
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", 3))
	requireNoError(t, err)
	stack, err := node.New(&node.Config{Name: "efsn", DataDir: filepath.Dir(directory), AuthAddr: "127.0.0.1", P2P: p2p.Config{PrivateKey: key, MaxPeers: 1, NoDiscovery: true, NoDial: true, ListenAddr: "127.0.0.1:0", NetRestrict: restrict}})
	requireNoError(t, err)
	defer stack.Close()
	config := ethconfig.Defaults
	config.Genesis = core.DefaultGenesisBlock()
	config.NetworkId, config.LightPeers = 99032659, 0
	config.DatabaseCache, config.DatabaseHandles = 128, 128
	config.TrieCleanCache, config.TrieDirtyCache = 32, 0
	config.NoPruning = true
	config.TxPool.Journal = ""
	datong.InitCheckPoints("")
	service, err := eth.New(stack, &config)
	requireNoError(t, err)
	requireNoError(t, stack.Start())
	if service.BlockChain().CurrentBlock().Hash() != expected.Hash() || service.BlockChain().CurrentHeader().Hash() != expected.Hash() || service.BlockChain().CurrentFastBlock().Hash() != expected.Hash() {
		t.Fatal("node startup changed restored chain head")
	}
	if service.IsMining() || len(stack.AccountManager().Wallets()) != 0 {
		t.Fatal("restore probe must have no validator accounts or mining")
	}
	client, err := stack.Attach()
	requireNoError(t, err)
	defer client.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	var head *types.Header
	requireNoError(t, client.CallContext(ctx, &head, "eth_getBlockByNumber", "latest", false))
	if head == nil || head.Hash() != expected.Hash() {
		t.Fatal("restored RPC head mismatch")
	}
	for _, wallet := range []struct {
		address, balance string
		nonce            uint64
	}{
		{"0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1", "3225543308109480158626", 233427},
		{"0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a", "12020102000000000000000", 0},
	} {
		address := common.HexToAddress(wallet.address)
		var balance string
		var ethereumBalance hexutil.Big
		var nonce hexutil.Uint64
		requireNoError(t, client.CallContext(ctx, &balance, "fsn_getBalance", common.SystemAssetID, address, "latest"))
		requireNoError(t, client.CallContext(ctx, &ethereumBalance, "eth_getBalance", address, "latest"))
		requireNoError(t, client.CallContext(ctx, &nonce, "eth_getTransactionCount", address, "latest"))
		if balance != wallet.balance || (*big.Int)(&ethereumBalance).String() != wallet.balance || uint64(nonce) != wallet.nonce {
			t.Fatal("restored RPC wallet differs from preserved balance or nonce")
		}
		t.Logf("restored wallet=%s liquidWei=%s nonce=%d", wallet.address, balance, nonce)
	}
	indexedQuery := false
	for _, height := range []uint64{1, 2700000, expected.Number.Uint64() - 256, expected.Number.Uint64()} {
		block := service.BlockChain().GetBlockByNumber(height)
		if block == nil {
			t.Fatal("restored historical block missing")
		}
		var logs []*types.Log
		requireNoError(t, client.CallContext(ctx, &logs, "eth_getLogs", map[string]interface{}{"blockHash": block.Hash()}))
		receipts := service.BlockChain().GetReceiptsByHash(block.Hash())
		expectedLogs := make([]*types.Log, 0)
		for _, receipt := range receipts {
			expectedLogs = append(expectedLogs, receipt.Logs...)
		}
		if len(logs) != len(expectedLogs) || len(logs) > 0 && !reflect.DeepEqual(logs, expectedLogs) {
			t.Fatal("restored RPC logs mismatch")
		}
		if height == 2700000 && len(expectedLogs) > 0 {
			address := expectedLogs[0].Address
			matching := make([]*types.Log, 0)
			for _, entry := range expectedLogs {
				if entry.Address == address {
					matching = append(matching, entry)
				}
			}
			var indexed []*types.Log
			requireNoError(t, client.CallContext(ctx, &indexed, "eth_getLogs", map[string]interface{}{"fromBlock": hexutil.EncodeUint64(height), "toBlock": hexutil.EncodeUint64(height), "address": address}))
			if !reflect.DeepEqual(indexed, matching) {
				t.Fatal("restored indexed RPC log query mismatch")
			}
			indexedQuery = true
		}
		if len(block.Transactions()) > 0 {
			var receipt *types.Receipt
			requireNoError(t, client.CallContext(ctx, &receipt, "eth_getTransactionReceipt", block.Transactions()[0].Hash()))
			if receipt == nil || receipt.BlockHash != block.Hash() {
				t.Fatal("restored RPC receipt lookup mismatch")
			}
		}
	}
	if !indexedQuery {
		t.Fatal("historical indexed log query was not exercised")
	}
	requireNoError(t, probeSnapshotPeer(service, stack))
	if service.IsMining() || service.BlockChain().CurrentBlock().Hash() != expected.Hash() {
		t.Fatal("read-only service exercise advanced the chain")
	}
	requireNoError(t, stack.Close())
}

func probeSnapshotPeer(service *eth.Ethereum, stack *node.Node) error {
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", 4))
	if err != nil {
		return err
	}
	restrict, err := netutil.ParseNetlist("127.0.0.0/8")
	if err != nil {
		return err
	}
	result := make(chan error, 1)
	peer := &p2p.Server{Config: p2p.Config{PrivateKey: key, Name: "snapshot-fetch-probe", MaxPeers: 1, NoDiscovery: true, NetRestrict: restrict, Protocols: []p2p.Protocol{{Name: eth.ProtocolName, Version: 63, Length: 17, Run: func(_ *p2p.Peer, rw p2p.MsgReadWriter) error {
		err := fetchSnapshotPeerData(service, rw)
		result <- err
		return err
	}}}}}
	if err := peer.Start(); err != nil {
		return err
	}
	defer peer.Stop()
	peer.AddPeer(stack.Server().Self())
	select {
	case err := <-result:
		return err
	case <-time.After(90 * time.Second):
		return fmt.Errorf("loopback snapshot peer timed out")
	}
}

func fetchSnapshotPeerData(service *eth.Ethereum, rw p2p.MsgReadWriter) error {
	chain := service.BlockChain()
	genesis := chain.Genesis()
	if err := p2p.Send(rw, eth.StatusMsg, snapshotPeerStatus{63, 99032659, genesis.Difficulty(), genesis.Hash(), genesis.Hash()}); err != nil {
		return err
	}
	var status snapshotPeerStatus
	if err := readSnapshotPeerPacket(rw, eth.StatusMsg, &status); err != nil {
		return err
	}
	head := chain.CurrentBlock()
	if status.Version != 63 || status.Network != 99032659 || status.Head != head.Hash() || status.Genesis != params.MainnetGenesisHash || status.TD.Cmp(chain.GetTd(head.Hash(), head.NumberU64())) != 0 {
		return fmt.Errorf("snapshot peer status mismatch")
	}
	for _, height := range []uint64{1, 2700000, head.NumberU64() - 256, head.NumberU64()} {
		request := struct {
			Origin, Amount, Skip uint64
			Reverse              bool
		}{height, 1, 0, false}
		if err := p2p.Send(rw, eth.GetBlockHeadersMsg, request); err != nil {
			return err
		}
		var headers []*types.Header
		if err := readSnapshotPeerPacket(rw, eth.BlockHeadersMsg, &headers); err != nil {
			return err
		}
		block := chain.GetBlockByNumber(height)
		if len(headers) != 1 || block == nil || headers[0].Hash() != block.Hash() {
			return fmt.Errorf("peer did not serve historical header %d", height)
		}
		if err := p2p.Send(rw, eth.GetBlockBodiesMsg, []common.Hash{block.Hash()}); err != nil {
			return err
		}
		var bodies []*types.Body
		if err := readSnapshotPeerPacket(rw, eth.BlockBodiesMsg, &bodies); err != nil {
			return err
		}
		if len(bodies) != 1 || types.DeriveSha(types.Transactions(bodies[0].Transactions), trie.NewStackTrie(nil)) != block.TxHash() || types.CalcUncleHash(bodies[0].Uncles) != types.CalcUncleHash(block.Uncles()) {
			return fmt.Errorf("peer historical body differs from preserved block")
		}
		if err := p2p.Send(rw, eth.GetReceiptsMsg, []common.Hash{block.Hash()}); err != nil {
			return err
		}
		var receipts []types.Receipts
		if err := readSnapshotPeerPacket(rw, eth.ReceiptsMsg, &receipts); err != nil {
			return err
		}
		if len(receipts) != 1 || types.DeriveSha(receipts[0], trie.NewStackTrie(nil)) != block.ReceiptHash() {
			return fmt.Errorf("peer historical receipt root mismatch")
		}
	}
	if err := p2p.Send(rw, eth.GetNodeDataMsg, []common.Hash{head.Root()}); err != nil {
		return err
	}
	var blobs []hexutil.Bytes
	if err := readSnapshotPeerPacket(rw, eth.NodeDataMsg, &blobs); err != nil {
		return err
	}
	if len(blobs) != 1 || !bytes.Equal(crypto.Keccak256(blobs[0]), head.Root().Bytes()) {
		return fmt.Errorf("peer did not serve the committed current state root")
	}
	return nil
}

func readSnapshotPeerPacket(rw p2p.MsgReadWriter, code uint64, output interface{}) error {
	for {
		message, err := rw.ReadMsg()
		if err != nil {
			return err
		}
		if message.Size > eth.ProtocolMaxMsgSize {
			return fmt.Errorf("peer response too large")
		}
		if message.Code == eth.GetBlockHeadersMsg {
			message.Discard()
			if err := p2p.Send(rw, eth.BlockHeadersMsg, []*types.Header{}); err != nil {
				return err
			}
			continue
		}
		if message.Code != code {
			message.Discard()
			return fmt.Errorf("unexpected peer message %d, wanted %d", message.Code, code)
		}
		return message.Decode(output)
	}
}
