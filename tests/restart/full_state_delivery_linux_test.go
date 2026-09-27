package restart

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type deliveryPoolState struct {
	Header  *types.Header
	Pending map[common.Address]types.Transactions
	Queued  map[common.Address]types.Transactions
	Own     peerPurchaseState
}

func (a *nodeRehearsalAPI) DeliveryPool() (deliveryPoolState, error) {
	result := deliveryPoolState{Header: a.service.BlockChain().CurrentHeader()}
	result.Pending, result.Queued = a.service.TxPool().Content()
	var err error
	result.Own, err = a.PurchaseState()
	return result, err
}

type deliveryHistoricalChain struct {
	*core.BlockChain
	head *types.Block
}

func (c deliveryHistoricalChain) CurrentBlock() *types.Block { return c.head }

func TestFullStateDeliveryHistoricalAdmission(t *testing.T) {
	rehearseHistoricalPurchaseAdmission(t, 15130098, 15130099, 8, common.HexToHash("0xdfea27eab0a6b3cd87782ff072176c2daa98222c9e764fdcf30c0fc75f30737f"), "BuyTicket start must be lower than latest block time + 3 hour")
}

func TestFullStateReconnectHistoricalAdmission(t *testing.T) {
	rehearseHistoricalPurchaseAdmission(t, 15130112, 15130113, 9, common.HexToHash("0xa13b447eb428b69640202b0257a0d61b7a43e53d03c5c5e4c6c5a531ab92db46"), "insufficient balance")
}

func rehearseHistoricalPurchaseAdmission(t *testing.T, before, after, nonce uint64, hash common.Hash, rejection string) {
	t.Helper()
	root := requireDeliveryRoot(t)
	requireFullStateCopy(t, filepath.Join(root, "verifier"))
	f, _, _ := openFullStateHandover(t, filepath.Join(root, "verifier"))
	var retained struct {
		Header *types.Header
		Saved  hexutil.Bytes
	}
	readHandoverJSON(t, filepath.Join(root, "diagnostic-saved-producer.json"), &retained)
	var tx types.Transaction
	requireNoError(t, tx.UnmarshalBinary(retained.Saved))
	if f.chain.CurrentBlock().Hash() != retained.Header.Hash() || tx.Nonce() != nonce || tx.Hash() != hash {
		t.Fatal("historical admission input differs from retained failure")
	}
	owner, err := types.Sender(types.LatestSigner(f.chain.Config()), &tx)
	requireNoError(t, err)
	var envelope common.FSNCallParam
	var purchase common.BuyTicketParam
	requireNoError(t, rlp.DecodeBytes(tx.Data(), &envelope))
	requireNoError(t, rlp.DecodeBytes(envelope.Data, &purchase))
	var records []map[string]interface{}
	for _, height := range []uint64{before, after, retained.Header.Number.Uint64()} {
		head := f.chain.GetBlockByNumber(height)
		if head == nil {
			t.Fatal("missing retained historical block")
		}
		state, err := f.chain.StateAt(head.Root(), head.MixDigest())
		requireNoError(t, err)
		config := core.DefaultTxPoolConfig
		config.Journal = ""
		pool := core.NewTxPool(config, f.chain.Config(), deliveryHistoricalChain{f.chain, head})
		admission := pool.AddRemotes([]*types.Transaction{&tx})[0]
		message := ""
		if admission != nil {
			message = admission.Error()
		} else {
			awaitRehearsal(t, 5*time.Second, func() bool { return pool.Status([]common.Hash{tx.Hash()})[0] == core.TxStatusPending })
		}
		records = append(records, map[string]interface{}{"Header": head.Header(), "Transaction": tx.Hash(), "Saved": retained.Saved, "Purchase": purchase, "CanonicalNonce": state.GetNonce(owner), "LiquidWei": state.GetBalance(common.SystemAssetID, owner).String(), "TimeLocks": state.GetTimeLockBalance(common.SystemAssetID, owner), "RemoteAdmissionError": message, "PoolStatus": pool.Status([]common.Hash{tx.Hash()})[0], "ObservedUnix": time.Now().Unix()})
		pool.Stop()
		requireNoError(t, writeStateExportJSON(filepath.Join(root, fmt.Sprintf("historical-admission-%d.json", height)), records[len(records)-1]))
		if height == before {
			requireErrorContains(t, admission, rejection)
		} else {
			requireNoError(t, admission)
		}
		t.Logf("identical remote purchase height=%d hash=%s nonce=%d error=%q", height, tx.Hash().Hex(), state.GetNonce(owner), message)
	}
	if f.chain.CurrentBlock().Hash() != retained.Header.Hash() {
		t.Fatal("historical admission moved the canonical head")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "historical-admission-complete.json"), records))
}

func requireDeliveryRoot(t *testing.T) string {
	t.Helper()
	root := os.Getenv("FUSION_RESTART_PURCHASE_DELIVERY")
	if root == "" {
		t.Skip("requires fresh disposable copies of the retained pending-purchase failure")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	return root
}

func TestFullStatePurchaseDirectDelivery(t *testing.T) {
	rehearseFullStatePurchaseDelivery(t, "direct")
}

func TestFullStatePurchasePeerReconnect(t *testing.T) {
	rehearseFullStatePurchaseDelivery(t, "reconnect")
}

func TestFullStatePurchaseAutomaticRebroadcast(t *testing.T) {
	rehearseFullStatePurchaseDelivery(t, "automatic")
}

func rehearseFullStatePurchaseDelivery(t *testing.T, mode string) {
	t.Helper()
	root := requireDeliveryRoot(t)
	reconnect := mode == "reconnect"
	originSubmission := mode != "direct"
	initialNonces, requiredNonces := [2]uint64{8, 26}, [2]uint64{9, 27}
	if mode == "automatic" {
		initialNonces, requiredNonces = [2]uint64{9, 38}, [2]uint64{11, 40}
	}
	var retained [2]struct {
		Header *types.Header
		Saved  hexutil.Bytes
	}
	var cleanup fullStateBlockLedger
	readHandoverJSON(t, filepath.Join(root, "blocks", "block-03.json"), &cleanup)
	anchor := types.NewBlockWithHeader(cleanup.Header)
	var nodes [2]*rehearsalNode
	var saved [2]*types.Transaction
	owners := [2]common.Address{common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
	for i, role := range []string{"producer", "verifier"} {
		readHandoverJSON(t, filepath.Join(root, "diagnostic-saved-"+role+".json"), &retained[i])
		if mode == "automatic" && retained[i].Header.Hash() != common.HexToHash("0xd94c46f9d7993ebbd0ac7e6d984e36b280724b30028edd04166e0b7d59f5a8f8") {
			t.Fatal("automatic retry requires the retained recurring failure at block 15130124")
		}
		saved[i] = new(types.Transaction)
		requireNoError(t, saved[i].UnmarshalBinary(retained[i].Saved))
		path := seedFullStateRecoveryNode(t, filepath.Join(root, role), anchor, byte(i+2))
		nodes[i] = startRehearsalNodeWithTimeout(t, path, 5*time.Minute)
		requireRehearsalHead(t, nodes[i].status(t), types.NewBlockWithHeader(retained[0].Header))
		state := readPeerPurchase(t, nodes[i])
		if !bytes.Equal(state.Saved, retained[i].Saved) || state.Nonce != initialNonces[i] || saved[i].Nonce() != initialNonces[i] || len(state.Pending)+len(state.Queued) != 0 {
			t.Fatal("reopened failure differs from retained saved intent and nonce")
		}
	}
	trace, err := os.OpenFile(filepath.Join(root, "delivery-pools.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	var previous []byte
	observe := func() {
		var pools [2]deliveryPoolState
		for i, node := range nodes {
			requireNoError(t, node.call(t, &pools[i], "lab_deliveryPool"))
		}
		encoded, err := json.Marshal(pools)
		requireNoError(t, err)
		if !bytes.Equal(previous, encoded) {
			requireNoError(t, json.NewEncoder(trace).Encode(map[string]interface{}{"ObservedUTC": time.Now().UTC(), "Nodes": pools}))
			previous = encoded
		}
	}
	observe()
	var submitted common.Hash
	target := nodes[1]
	if originSubmission {
		connectRehearsalPeer(t, nodes[0], nodes[1])
		awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
		target = nodes[0]
	}
	requireNoError(t, target.call(t, &submitted, "eth_sendRawTransaction", retained[0].Saved))
	if submitted != saved[0].Hash() {
		t.Fatal("direct recipient returned a different transaction hash")
	}
	var recipient deliveryPoolState
	requireNoError(t, nodes[1].call(t, &recipient, "lab_deliveryPool"))
	if originSubmission {
		time.Sleep(time.Second)
		requireNoError(t, nodes[1].call(t, &recipient, "lab_deliveryPool"))
		sender := readPeerPurchase(t, nodes[0])
		if len(recipient.Pending[owners[0]])+len(recipient.Queued[owners[0]]) != 0 || !bytes.Equal(sender.Saved, retained[0].Saved) || len(sender.Pending) != 1 || sender.Pending[0].Hash() != submitted {
			t.Fatal("expected unchanged saved purchase only in originating pool before recipient mining readiness")
		}
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "unready-recipient.json"), recipient))
	} else {
		if len(recipient.Pending[owners[0]]) != 1 || recipient.Pending[owners[0]][0].Hash() != submitted {
			t.Fatal("directly submitted transaction is absent from recipient pending pool")
		}
		if sender := readPeerPurchase(t, nodes[0]); !bytes.Equal(sender.Saved, retained[0].Saved) || len(sender.Pending)+len(sender.Queued) != 0 {
			t.Fatal("direct delivery changed the originating node's saved record or pool")
		}
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "direct-recipient.json"), recipient))
		connectRehearsalPeer(t, nodes[0], nodes[1])
		awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	}
	observe()
	for _, node := range nodes {
		requireNoError(t, node.call(t, nil, "miner_start", 1))
		awaitRehearsal(t, 20*time.Second, func() bool { return node.status(t).Mining })
	}
	if reconnect {
		requireNoError(t, nodes[1].call(t, &recipient, "lab_deliveryPool"))
		if len(recipient.Pending[owners[0]])+len(recipient.Queued[owners[0]]) != 0 {
			t.Fatal("purchase arrived before the deliberate peer reconnect")
		}
		var info p2p.NodeInfo
		requireNoError(t, nodes[1].call(t, &info, "admin_nodeInfo"))
		var removed bool
		requireNoError(t, nodes[0].call(t, &removed, "admin_removePeer", info.Enode))
		if !removed {
			t.Fatal("static peer removal failed")
		}
		awaitMinerPartitionPeers(t, nodes[0], nodes[1], 0, 10*time.Second)
		connectRehearsalPeer(t, nodes[0], nodes[1])
		awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 10*time.Second)
		awaitRehearsal(t, 15*time.Second, func() bool {
			requireNoError(t, nodes[1].call(t, &recipient, "lab_deliveryPool"))
			for _, tx := range recipient.Pending[owners[0]] {
				if tx.Hash() == submitted {
					return true
				}
			}
			var receipt *types.Receipt
			requireNoError(t, nodes[1].call(t, &receipt, "eth_getTransactionReceipt", submitted))
			return receipt != nil
		})
		requireNoError(t, writeStateExportJSON(filepath.Join(root, "reconnected-recipient.json"), recipient))
		observe()
		t.Log("same node identities disconnected and reconnected after both mining services became ready; pending purchase delivered through ordinary peer sync without recipient RPC submission")
	}
	for _, node := range []*rehearsalNode{nodes[1], nodes[0]} {
		requireNoError(t, node.call(t, nil, "miner_startAutoBuyTicket"))
	}
	progress := awaitContinuousMinerProgressObserved(t, nodes[0], nodes[1], owners, requiredNonces, retained[0].Header.Number.Uint64(), 150*time.Second, observe)
	for i, tx := range saved {
		for _, node := range nodes {
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if receipt == nil {
				t.Fatal("exact saved purchase has no canonical receipt")
			}
			block := readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64())
			requirePeerNativePurchase(t, receipt, block, tx, owners[i])
		}
	}
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	observe()
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "delivery-stopped-purchases.json"), stopped))
	artifacts := filepath.Join(root, "delivery-blocks")
	count := captureFullStateColdSuffixAt(t, root, final, artifacts)
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	var recovery struct {
		Final         *types.Header
		Contributions types.Transactions
	}
	readHandoverJSON(t, filepath.Join(root, "funding-recovery.json"), &recovery)
	if len(recovery.Contributions) != 2 {
		t.Fatal("expected exact prior funding manifest")
	}
	allowed := make(map[common.Hash]uint64)
	for _, tx := range recovery.Contributions {
		allowed[tx.Hash()] = recovery.Final.Number.Uint64() - 1
	}
	auditFullStateParticipantTransfers(t, artifacts, count, allowed)
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("cold-intent-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			state, err := f.chain.State()
			requireNoError(t, err)
			key := append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...)
			exists, err := f.db.Has(key)
			requireNoError(t, err)
			if exists != (len(stopped[i].Saved) > 0) || state.GetNonce(owners[i]) != stopped[i].Nonce {
				t.Fatal("cold intent presence or nonce differs")
			}
			if exists {
				data, err := f.db.Get(key)
				requireNoError(t, err)
				if !bytes.Equal(data, stopped[i].Saved) {
					t.Fatal("cold saved bytes changed")
				}
			}
			recordFundingInventory(t, root, role+"-delivery-final", f, append([]common.Address{f.owner}, owners[:]...), saved)
		}) {
			t.Fatal("cold purchase intent verification failed")
		}
	}
	direct := submitted
	if originSubmission {
		direct = common.Hash{}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "delivery-result.json"), map[string]interface{}{"Before": retained[0].Header, "Progress": progress.Header(), "Final": final.Header(), "Blocks": count, "ExactSavedPurchases": saved, "RequiredFreshNonces": requiredNonces, "DirectSubmission": direct, "PeerReconnect": reconnect, "AutomaticRebroadcast": mode == "automatic", "NewFunding": false, "NonceGapExercised": false}))
	t.Logf("exact saved purchase delivery and both-owner replenishment passed; mode=%s cold suffix=%d final=%d %s", mode, count, final.NumberU64(), final.Hash().Hex())
}
