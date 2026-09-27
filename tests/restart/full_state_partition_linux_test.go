package restart

import (
	"bytes"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type fullStateRepairResult struct {
	Owner             common.Address
	CanonicalNonce    uint64
	SavedNonce        uint64
	SavedHash         common.Hash
	OriginalsIncluded int
	Successors        int
	FundingFailure    string
	Funding           map[common.Hash]uint64
	Final             common.Hash
}

func TestFullStatePartitionRepair(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_FULL_STATE_PARTITION")
	if root == "" {
		t.Skip("requires fresh verified complete-state partition copies")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and isolated node rehearsal required")
	}
	cleanup := prepareFullStateOutage(t, root)
	installFullStateHistory(t, root)
	anchor := prepareFullStateParticipant(t, root, cleanup)
	rehearseFullStatePartitionRepair(t, root, cleanup, anchor, false)
}

func rehearseFullStatePartitionRepair(t *testing.T, root string, cleanup, anchor *types.Block, funded bool) {
	t.Helper()
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), cleanup, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), cleanup, 3)}
	timeout := 12 * time.Minute
	if funded {
		timeout = 16 * time.Minute
	}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], timeout), startRehearsalNodeWithTimeout(t, paths[1], timeout)}
	owners := [2]common.Address{common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	initial := [2]uint64{readPeerPurchase(t, nodes[0]).Nonce, readPeerPurchase(t, nodes[1]).Nonce}
	for _, node := range nodes {
		startCompetingMiner(t, node)
	}
	warm := awaitContinuousMinerProgress(t, nodes[0], nodes[1], owners, initial, anchor.NumberU64(), 120*time.Second)
	logLiveRepairTickets(t, nodes[0], owners, warm, "full-state-before-outage")
	requireFullStatePartitionReserve(t, root, nodes, owners, warm)
	originals := [2]map[uint64]*types.Transaction{make(map[uint64]*types.Transaction), make(map[uint64]*types.Transaction)}
	heal := dropRehearsalPackets(t, "match", "ip", "dst", "127.0.0.0/8")
	cut := time.Now()
	for time.Since(cut) < 90*time.Second {
		requireContinuousMiners(t, nodes[0], nodes[1])
		for i, node := range nodes {
			captureLivePurchases(t, node, owners[i], originals[i])
		}
		time.Sleep(500 * time.Millisecond)
	}
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 0, 5*time.Second)
	var isolated [2]types.Blocks
	floor := uint64(0)
	base := cleanup.NumberU64() - 3
	for i, node := range nodes {
		head := node.status(t)
		if head.Number <= warm.NumberU64()+2 {
			t.Fatal("isolated producer did not advance multiple blocks")
		}
		floor = common.MaxUint64(floor, head.Number)
		for number := base + 1; number <= head.Number; number++ {
			block := readRecoveryNodeBlock(t, node, number)
			isolated[i] = append(isolated[i], block)
			for _, tx := range block.Transactions() {
				retainLivePurchase(t, owners[i], originals[i], tx)
			}
		}
		logLiveRepairTickets(t, node, owners, isolated[i][len(isolated[i])-1], "full-state-isolated")
	}
	fork := uint64(0)
	for i := 0; i < len(isolated[0]) && i < len(isolated[1]); i++ {
		if isolated[0][i].Hash() != isolated[1][i].Hash() {
			fork = isolated[0][i].NumberU64()
			break
		}
	}
	if fork <= anchor.NumberU64() {
		t.Fatal("partition did not create competing descendants of the shared funded prefix")
	}
	t.Logf("full-state partition isolated duration=%s fork=%d heads=%d/%d hashes=%s/%s", time.Since(cut), fork, base+uint64(len(isolated[0])), base+uint64(len(isolated[1])), isolated[0][len(isolated[0])-1].Hash().Hex(), isolated[1][len(isolated[1])-1].Hash().Hex())
	for i, role := range []string{"producer", "verifier"} {
		path := filepath.Join(root, "isolated-"+role+".rlp")
		encoded, err := rlp.EncodeToBytes(isolated[i])
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(path, encoded, 0600))
	}
	retained := [2]map[common.Hash]*types.Block{make(map[common.Hash]*types.Block), make(map[common.Hash]*types.Block)}
	for i := range isolated {
		for _, block := range isolated[i] {
			retained[i][block.Hash()] = block
		}
	}
	observe := func() {
		for i, node := range nodes {
			previous := len(retained[i])
			captureObservedBranch(t, node, node.status(t).Hash, base, retained[i])
			if len(retained[i]) != previous {
				blocks := retainObservedBlocks(t, filepath.Join(root, fmt.Sprintf("observed-%d.rlp", i)), retained[i])
				for _, block := range blocks {
					for _, tx := range block.Transactions() {
						retainLivePurchase(t, owners[i], originals[i], tx)
					}
				}
			}
		}
	}
	observe()
	heal()
	gap := awaitLivePurchaseGapObserved(t, nodes, owners, originals, floor, observe)
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	logContinuousPurchaseState(t, nodes[0], nodes[1])
	logLiveRepairTickets(t, nodes[0], owners, gap.head, "full-state-before-repair")
	t.Logf("full-state partition stable gap node=%d owner=%s canonical=%d saved=%d hash=%s common=%d %s", gap.index+1, owners[gap.index].Hex(), gap.nonce, gap.saved.Nonce(), gap.saved.Hash().Hex(), gap.head.NumberU64(), gap.head.Hash().Hex())
	branch := retainObservedBlocks(t, filepath.Join(root, "repair-branch.rlp"), retained[gap.index])
	result := repairFullStateGap(t, root, nodes, owners, gap, originals[gap.index], branch, funded)
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	final := awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	var stopped [2]peerPurchaseState
	for i, node := range nodes {
		stopped[i] = readPeerPurchase(t, node)
		requireRehearsalHead(t, node.status(t), final)
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	count := captureFullStateColdSuffix(t, root, final)
	auditFullStateHandover(t, filepath.Join(root, "producer"), filepath.Join(root, "blocks"), 3)
	auditFullStateParticipantTransfers(t, filepath.Join(root, "blocks"), count, result.Funding)
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("isolated-ledger-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			state, err := f.chain.State()
			requireNoError(t, err)
			key := append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...)
			exists, err := f.db.Has(key)
			requireNoError(t, err)
			if exists != (len(stopped[i].Saved) > 0) || state.GetNonce(owners[i]) != stopped[i].Nonce {
				t.Fatal("cold automatic record presence or nonce changed")
			}
			if exists {
				saved, err := f.db.Get(key)
				requireNoError(t, err)
				if !bytes.Equal(saved, stopped[i].Saved) {
					t.Fatal("cold saved automatic purchase bytes changed")
				}
			}
			t.Logf("full-state partition cold intent role=%s nonce=%d saved-bytes=%d unchanged", role, stopped[i].Nonce, len(stopped[i].Saved))
			artifacts := filepath.Join(root, "isolated-"+role)
			requireNoError(t, os.Mkdir(artifacts, 0700))
			for _, block := range isolated[i] {
				recordFullStateHandoverBlock(t, f, artifacts, base, block)
			}
			auditFullStateHandover(t, filepath.Join(root, role), artifacts, 3)
			auditFullStateParticipant(t, artifacts, len(isolated[i]))
		}) {
			t.Fatal("isolated branch account audit failed")
		}
	}
	result.Final = final.Hash()
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "repair-result.json"), result))
	t.Logf("full-state partition cold accounting complete: final=%d %s state=%s tickets=%s blocks=%d originals=%d successors=%d funding-failure=%q; both canonical databases and both isolated branches verified", final.NumberU64(), final.Hash().Hex(), final.Root().Hex(), final.MixDigest().Hex(), count, result.OriginalsIncluded, result.Successors, result.FundingFailure)
	if result.FundingFailure != "" {
		t.Fatalf("complete-state manual repair remains unfunded: %s; evidence and cold accounting retained", result.FundingFailure)
	}
}

func repairFullStateGap(t *testing.T, root string, nodes [2]*rehearsalNode, owners [2]common.Address, gap livePurchaseGap, originals map[uint64]*types.Transaction, branch types.Blocks, funded bool) fullStateRepairResult {
	t.Helper()
	result := fullStateRepairResult{Owner: owners[gap.index], CanonicalNonce: gap.nonce, SavedNonce: gap.saved.Nonce(), SavedHash: gap.saved.Hash()}
	path := filepath.Join(root, "repair")
	requireNoError(t, os.Mkdir(path, 0700))
	saved, err := gap.saved.MarshalBinary()
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "saved.rlp"), saved, 0600))
	var retrieved types.Transactions
	for nonce := gap.nonce; nonce < gap.saved.Nonce(); nonce++ {
		tx := originals[nonce]
		if tx == nil {
			t.Fatal("missing original purchase; cannot construct a safe manual repair")
		}
		var old *types.Block
		for _, block := range branch {
			for _, candidate := range block.Transactions() {
				if candidate.Hash() == tx.Hash() {
					old = block
				}
			}
		}
		if old == nil {
			t.Fatal("missing displaced block for original purchase")
		}
		tx = requireDisplacedPurchaseRPC(t, nodes[gap.index], old, tx)
		data, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(path, fmt.Sprintf("original-%d.rlp", nonce)), data, 0600))
		validateLiveRepairPurchase(t, nodes[gap.index], tx)
		retrieved = append(retrieved, tx)
	}
	t.Logf("full-state repair retrieved all %d missing original purchases before submission", len(retrieved))
	if funded {
		result.Funding = fundUninterruptedFullStateGap(t, root, nodes, owners, gap, retrieved[0])
	}
	for _, tx := range retrieved {
		nonce := tx.Nonce()
		state := readPeerPurchase(t, nodes[gap.index])
		if state.Nonce != nonce || !bytes.Equal(state.Saved, saved) || len(state.Pending)+len(state.Queued) != 0 {
			t.Fatal("repair nonce, saved intent or empty pool changed")
		}
		validateLiveRepairPurchase(t, nodes[gap.index], tx)
		failure := submitFullStateRepair(t, path, nodes, owners, gap, tx)
		if failure != "" {
			result.FundingFailure = failure
			return result
		}
		block := awaitLiveRepairReceipt(t, nodes, tx, result.Owner)
		result.OriginalsIncluded++
		t.Logf("full-state manual original included nonce=%d hash=%s block=%d %s", nonce, tx.Hash().Hex(), block.NumberU64(), block.Hash().Hex())
	}
	savedBlock := awaitLiveRepairReceipt(t, nodes, gap.saved, result.Owner)
	required := [2]uint64{readPeerPurchase(t, nodes[0]).Nonce, readPeerPurchase(t, nodes[1]).Nonce}
	required[gap.index] = gap.saved.Nonce() + 2
	resumed := awaitContinuousMinerProgress(t, nodes[0], nodes[1], owners, required, savedBlock.NumberU64(), 120*time.Second)
	for number := savedBlock.NumberU64() + 1; number <= resumed.NumberU64(); number++ {
		for _, tx := range readRecoveryNodeBlock(t, nodes[0], number).Transactions() {
			owner, err := types.Sender(types.LatestSignerForChainID(tx.ChainId()), tx)
			requireNoError(t, err)
			if owner == result.Owner && tx.IsBuyTicketTx() && tx.Nonce() > gap.saved.Nonce() {
				awaitLiveRepairReceipt(t, nodes, tx, owner)
				result.Successors++
			}
		}
	}
	if result.Successors < 2 {
		t.Fatal("manual repair did not resume two fresh automatic purchases")
	}
	t.Logf("full-state manual repair recovered exact saved=%s originals=%d automatic-successors=%d", gap.saved.Hash().Hex(), result.OriginalsIncluded, result.Successors)
	return result
}

func submitFullStateRepair(t *testing.T, path string, nodes [2]*rehearsalNode, owners [2]common.Address, gap livePurchaseGap, tx *types.Transaction) string {
	t.Helper()
	data, err := tx.MarshalBinary()
	requireNoError(t, err)
	saved, err := gap.saved.MarshalBinary()
	requireNoError(t, err)
	started := time.Now()
	for {
		requireContinuousMiners(t, nodes[0], nodes[1])
		state := readPeerPurchase(t, nodes[gap.index])
		if state.Nonce != tx.Nonce() || !bytes.Equal(state.Saved, saved) || len(state.Pending)+len(state.Queued) != 0 {
			t.Fatal("repair state changed while waiting for ordinary ticket return")
		}
		var hash common.Hash
		err = nodes[gap.index].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(data))
		if err == nil {
			if hash != tx.Hash() {
				t.Fatal("repair submission changed signed transaction identity")
			}
			return ""
		}
		if !strings.Contains(err.Error(), "insufficient balance") {
			t.Fatalf("unexpected manual purchase rejection: %v", err)
		}
		head := nodes[gap.index].status(t).Number
		funds := readPartitionFunds(t, nodes[gap.index], owners[:], head)
		account := funds.Accounts[owners[gap.index]]
		var envelope common.FSNCallParam
		var purchase common.BuyTicketParam
		requireNoError(t, rlp.DecodeBytes(tx.Data(), &envelope))
		requireNoError(t, rlp.DecodeBytes(envelope.Data, &purchase))
		start := common.MaxUint64(purchase.Start, uint64(time.Now().Unix()))
		coverage := account.TimeLockBalancesVal[0].GetSpendableValue(start, purchase.End)
		gas := new(big.Int).Mul(new(big.Int).SetUint64(tx.Gas()), tx.GasPrice())
		needed := new(big.Int).Set(gas)
		if coverage.Cmp(decimal(t, "5000000000000000000000")) < 0 {
			needed.Add(needed, decimal(t, "5000000000000000000000"))
		}
		if account.BalancesVal[0].Cmp(needed) >= 0 {
			t.Fatal("pool rejection disagrees with the sampled liquid and interval funding")
		}
		live := 0
		for _, ticket := range funds.Tickets {
			if ticket.Owner == owners[gap.index] {
				live++
			}
		}
		t.Logf("full-state repair unfunded nonce=%d height=%d owner=%s tickets=%d liquid-wei=%s coverage-wei=%s needed-liquid-wei=%s wait=%s rejection=%v", tx.Nonce(), head, owners[gap.index].Hex(), live, account.BalancesVal[0], coverage, needed, time.Since(started), err)
		if live == 0 || time.Since(started) >= 120*time.Second {
			snapshot := map[string]interface{}{"Header": funds.Block.Header(), "Accounts": funds.Accounts, "Tickets": funds.Tickets, "Transaction": tx, "WindowStart": start, "WindowEnd": purchase.End, "CoverageWei": coverage.String(), "GasBudgetWei": gas.String(), "RequiredLiquidWei": needed.String(), "PoolError": err.Error()}
			requireNoError(t, writeStateExportJSON(filepath.Join(path, fmt.Sprintf("unfunded-%d.json", tx.Nonce())), snapshot))
			return fmt.Sprintf("nonce=%d tickets=%d liquid=%s coverage=%s needed-liquid=%s: %v", tx.Nonce(), live, account.BalancesVal[0], coverage, needed, err)
		}
		time.Sleep(2 * time.Second)
	}
}
