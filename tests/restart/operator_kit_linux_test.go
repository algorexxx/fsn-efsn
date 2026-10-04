package restart

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func rehearseOperatorKit(t *testing.T) {
	if !filepath.IsAbs(os.Getenv("FUSION_RESTART_EFSN_COMMAND")) {
		t.Skip("requires the separately verified efsn console executable")
	}
	entrant := common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")
	pair := seedDenseMinerPairWithWindow(t, "50000000000000000000000", 2, core.GenesisAlloc{
		entrant: {Balance: decimal(t, "50000000000000000000000")},
	}, uint64(time.Now().Unix())-5000, 0)
	shared := pair.miners[0].chain.CurrentBlock()
	producer := pair.miners[1]
	accepted := buildAnchorBranch(t, producer, 4, 120)
	for len(accepted) < 12 {
		state, err := producer.chain.State()
		requireNoError(t, err)
		tickets, err := state.AllTickets()
		requireNoError(t, err)
		if tickets.NumberOfTicketsByAddress(pair.miners[0].owner) == 0 {
			break
		}
		accepted = append(accepted, buildAnchorBranch(t, producer, 1, 120)...)
	}
	state, err := producer.chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTicketsByAddress(pair.miners[0].owner) != 0 || tickets.NumberOfTicketsByAddress(entrant) != 0 {
		t.Fatal("fixture must retire the backup tickets and leave the entrant without a ticket")
	}
	closeOperatorKitSeed(t, pair, 0, accepted[0], 3)
	closeOperatorKitSeed(t, pair, 1, accepted[0], 2)
	restored := restoreOperatorKitSeed(t, pair.paths[0], shared, pair.miners[0].chain.Genesis().Hash())
	donation := startRehearsalNodeWithTimeout(t, pair.paths[1], 8*time.Minute)
	joining := startRehearsalNodeWithTimeout(t, restored, 8*time.Minute)
	var sourceInfo, joiningInfo struct{ ID, Enode string }
	runOperatorConsole(t, donation, "admin.nodeInfo", &sourceInfo)
	runOperatorConsole(t, joining, "admin.nodeInfo", &joiningInfo)
	if sourceInfo.ID == joiningInfo.ID || sourceInfo.ID == "" || joiningInfo.ID == "" {
		t.Fatal("fresh entrant must have a distinct P2P identity")
	}
	var added bool
	runOperatorConsole(t, joining, fmt.Sprintf("admin.addPeer(%q)", sourceInfo.Enode), &added)
	if !added {
		t.Fatal("operator static fallback did not add the peer")
	}
	awaitRehearsal(t, 90*time.Second, func() bool { return joining.status(t).Hash == donation.status(t).Hash })
	requireRehearsalHead(t, joining.status(t), accepted[len(accepted)-1])
	var ready struct {
		Genesis common.Hash
		Anchor  common.Hash
		Syncing bool
		Mining  bool
		AutoBuy bool
		Balance string
		Nonce   uint64
	}
	probe := fmt.Sprintf("({genesis:eth.getBlock(0).hash,anchor:eth.getBlock(%d).hash,syncing:eth.syncing,mining:eth.mining,autoBuy:fsn.isAutoBuyTicket(),balance:fsn.getBalance(%q,%q,'latest'),nonce:eth.getTransactionCount(%q,'latest')})", accepted[0].NumberU64(), common.SystemAssetID.Hex(), entrant.Hex(), entrant.Hex())
	runOperatorConsole(t, joining, probe, &ready)
	if ready.Genesis != pair.miners[0].chain.Genesis().Hash() || ready.Anchor != accepted[0].Hash() || ready.Syncing || ready.Mining || ready.AutoBuy || ready.Balance != "50000000000000000000000" || ready.Nonce != 0 {
		t.Fatalf("operator console identity/funding preflight differs: %+v", ready)
	}
	startOperatorMiner(t, donation)
	awaitRehearsal(t, 60*time.Second, func() bool { return joining.status(t).Number > accepted[len(accepted)-1].NumberU64() })
	var purchase common.Hash
	runOperatorConsole(t, joining, fmt.Sprintf("fsntx.buyTicket({from:%q})", entrant.Hex()), &purchase)
	var receipt *types.Receipt
	awaitRehearsal(t, 60*time.Second, func() bool {
		requireNoError(t, joining.call(t, &receipt, "eth_getTransactionReceipt", purchase))
		return receipt != nil
	})
	first := readRecoveryNodeBlock(t, joining, receipt.BlockNumber.Uint64())
	var firstTx *types.Transaction
	for _, tx := range first.Transactions() {
		if tx.Hash() == purchase {
			firstTx = tx
		}
	}
	if firstTx == nil {
		t.Fatal("first operator purchase is absent from its canonical block")
	}
	requirePeerNativePurchase(t, receipt, first, firstTx, entrant)
	var consoleReceipt struct{ TransactionHash, BlockHash common.Hash }
	runOperatorConsole(t, joining, fmt.Sprintf("eth.getTransactionReceipt(%q)", purchase.Hex()), &consoleReceipt)
	if consoleReceipt.TransactionHash != purchase || consoleReceipt.BlockHash != first.Hash() {
		t.Fatal("console receipt differs from the verified native purchase")
	}
	owners := [2]common.Address{producer.owner, entrant}
	nonces := [2]uint64{readPeerPurchase(t, donation).Nonce, 1}
	startOperatorMiner(t, joining)
	head := awaitContinuousMinerProgress(t, donation, joining, owners, nonces, first.NumberU64(), 120*time.Second)
	awaitRehearsal(t, 30*time.Second, func() bool {
		produced := make(map[common.Address]bool)
		limit := joining.status(t).Number
		for number := first.NumberU64() + 1; number <= limit; number++ {
			produced[readRecoveryNodeBlock(t, joining, number).Coinbase()] = true
		}
		return produced[owners[0]] && produced[owners[1]]
	})
	for _, node := range []*rehearsalNode{donation, joining} {
		runOperatorConsole(t, node, "(miner.stopAutoBuyTicket(),miner.stop(),{mining:eth.mining,buying:fsn.isAutoBuyTicket()})", nil)
	}
	final := awaitStoppedPartitionHead(t, donation, joining)
	if final.NumberU64() > accepted[len(accepted)-1].NumberU64()+64 {
		t.Fatal("operator rehearsal exceeded its 64 live-block bound")
	}
	var suffix types.Blocks
	for number := shared.NumberU64() + 1; number <= final.NumberU64(); number++ {
		suffix = append(suffix, readRecoveryNodeBlock(t, joining, number))
	}
	for _, node := range []*rehearsalNode{donation, joining} {
		requireRehearsalHead(t, node.status(t), final)
		requireAutomaticSyncLookups(t, node, suffix, nil)
		requireOperatorKitFinal(t, node, suffix, owners, nonces, purchase, first.NumberU64())
		before := readPeerPurchase(t, node)
		node.stop(t, false)
		cold := startRehearsalNodeWithTimeout(t, node.path, 8*time.Minute)
		requireRehearsalHead(t, cold.status(t), final)
		requireAutomaticSyncStopped(t, cold.status(t))
		requireAutomaticSyncLookups(t, cold, suffix, nil)
		requireOperatorKitFinal(t, cold, suffix, owners, nonces, purchase, first.NumberU64())
		after := readPeerPurchase(t, cold)
		if before.Nonce != after.Nonce || !bytes.Equal(before.Saved, after.Saved) {
			t.Fatal("cold restart changed the account nonce or saved automatic purchase")
		}
		runOperatorConsole(t, cold, "({number:eth.blockNumber,hash:eth.getBlock('latest').hash,mining:eth.mining,buying:fsn.isAutoBuyTicket()})", nil)
		cold.stop(t, false)
	}
	t.Logf("operator kit: restored height=%d anchor=%s first purchase=%s both replenished through=%d final=%d hash=%s; backup process never started, two distinct live producers and both cold commitments/lookups passed", shared.NumberU64(), accepted[0].Hash().Hex(), purchase.Hex(), head.NumberU64(), final.NumberU64(), final.Hash().Hex())
}

func requireOperatorKitFinal(t *testing.T, node *rehearsalNode, blocks types.Blocks, owners [2]common.Address, nonces [2]uint64, first common.Hash, floor uint64) {
	t.Helper()
	produced, replenished := make(map[common.Address]bool), make(map[common.Address]bool)
	foundFirst := false
	for _, block := range blocks {
		if block.NumberU64() > floor {
			produced[block.Coinbase()] = true
		}
		for _, tx := range block.Transactions() {
			if tx.Hash() == first {
				foundFirst = true
			}
			if !tx.IsBuyTicketTx() {
				continue
			}
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			requirePeerNativePurchase(t, receipt, block, tx, owner)
			for i, address := range owners {
				if owner == address && tx.Nonce() >= nonces[i] {
					replenished[owner] = true
				}
			}
		}
	}
	if !foundFirst || !produced[owners[0]] || !produced[owners[1]] || !replenished[owners[0]] || !replenished[owners[1]] {
		t.Fatal("settled canonical history lost first purchase, production or replenishment")
	}
}

func closeOperatorKitSeed(t *testing.T, pair *denseMinerPair, index int, anchor *types.Block, key byte) {
	t.Helper()
	closeTwoMinerSeed(t, pair.paths[index], pair.miners[index], anchor, key)
	path := filepath.Join(pair.paths[index], "lab.json")
	var config nodeRehearsalConfig
	readHandoverJSON(t, path, &config)
	config.DenseGenesis = pair.genesis
	data, err := json.MarshalIndent(config, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(path, data, 0600))
}

func startOperatorMiner(t *testing.T, node *rehearsalNode) {
	t.Helper()
	runOperatorConsole(t, node, "miner.start(1)", nil)
	awaitRehearsal(t, 20*time.Second, func() bool { return node.status(t).Mining })
	runOperatorConsole(t, node, "(miner.startAutoBuyTicket(),{mining:eth.mining,buying:fsn.isAutoBuyTicket()})", nil)
}

func restoreOperatorKitSeed(t *testing.T, source string, head *types.Block, genesis common.Hash) string {
	t.Helper()
	root := t.TempDir()
	identity := filepath.Join(root, "identity.json")
	requireNoError(t, writeStateExportJSON(identity, map[string]interface{}{"genesis": genesis, "head": head.Header()}))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(source, "anchor-lab", "chaindata"), 16, 16, "", true)
	requireNoError(t, err)
	defer db.Close()
	packagePath := filepath.Join(root, "package")
	runOperatorPackage(t, "pack", "--source", filepath.Join(source, "anchor-lab", "chaindata"), "--destination", packagePath, "--identity", identity)
	manifest, err := os.ReadFile(filepath.Join(packagePath, "manifest.json"))
	requireNoError(t, err)
	var inventory struct{ Bytes uint64 }
	requireNoError(t, json.Unmarshal(manifest, &inventory))
	if inventory.Bytes > 64*1024*1024 {
		t.Fatal("synthetic operator package exceeds its 64 MiB bound")
	}
	digest := sha256.Sum256(manifest)
	dataDir := filepath.Join(root, "fresh-node")
	requireNoError(t, os.Mkdir(dataDir, 0700))
	runOperatorPackage(t, "restore", "--source", packagePath, "--destination", filepath.Join(dataDir, "anchor-lab"), "--manifest-sha256", hex.EncodeToString(digest[:]))
	if _, err := os.Stat(filepath.Join(dataDir, "anchor-lab", "restored.json")); err != nil {
		t.Fatal("restore did not produce its verified completion marker")
	}
	data, err := os.ReadFile(filepath.Join(source, "lab.json"))
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(dataDir, "lab.json"), data, 0600))
	t.Logf("verified fresh synthetic restore: bytes=%d manifest=%x; package contains only flat LevelDB files", inventory.Bytes, digest)
	return dataDir
}

func runOperatorPackage(t *testing.T, arguments ...string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	args := append([]string{"snapshot_package.py"}, arguments...)
	args = append(args, "--reserve-bytes", "5368709120")
	output, err := exec.CommandContext(ctx, "python3", args...).CombinedOutput()
	t.Logf("operator package %s:\n%s", arguments[0], output)
	requireNoError(t, err)
}

func runOperatorConsole(t *testing.T, node *rehearsalNode, expression string, result interface{}) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	script := "console.log('OPERATOR_RESULT '+JSON.stringify(" + expression + "))"
	output, err := exec.CommandContext(ctx, os.Getenv("FUSION_RESTART_EFSN_COMMAND"), "--datadir", filepath.Join(node.path, "console"), "--exec", script, "attach", filepath.Join(node.path, "lab.ipc")).CombinedOutput()
	t.Logf("operator console %s:\n%s", expression, output)
	requireNoError(t, err)
	for _, line := range strings.Split(string(output), "\n") {
		if strings.HasPrefix(line, "OPERATOR_RESULT ") {
			if result != nil {
				requireNoError(t, json.Unmarshal([]byte(strings.TrimPrefix(line, "OPERATOR_RESULT ")), result))
			}
			return
		}
	}
	t.Fatal("console did not return its explicit success marker")
}
