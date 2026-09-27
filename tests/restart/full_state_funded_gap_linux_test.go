package restart

import (
	"bytes"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateFundedGapRepair(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	expected := common.HexToHash("0x1a52a5d9fec08c0c5aa2adddf62dcaf115991f74919877c88e6756b771d67aaf")
	owners := [2]common.Address{common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
	var head, cleanup *types.Block
	var saved [2]*types.Transaction
	var transfers types.Transactions
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			head = f.chain.CurrentBlock()
			cleanup = f.chain.GetBlockByNumber(15130083)
			if head.Hash() != expected {
				t.Fatal("funded repair must start at the retained partition failure")
			}
			state, err := f.chain.State()
			requireNoError(t, err)
			if state.GetNonce(owners[0]) != 18 || state.GetNonce(owners[1]) != 7 || state.GetNonce(f.owner) != 233429 {
				t.Fatal("retained funding nonces changed")
			}
			data, err := f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...))
			requireNoError(t, err)
			saved[i] = new(types.Transaction)
			requireNoError(t, saved[i].UnmarshalBinary(data))
			if saved[i].Nonce() != []uint64{18, 14}[i] {
				t.Fatal("retained saved purchase nonce changed")
			}
			if i == 0 {
				donation := *f
				selectHandoverSuccessor(t, &donation, funding)
				pool := f.newPool(t)
				requireNoError(t, pool.AddLocal(saved[0]))
				for j, sponsor := range []*fixture{f, &donation} {
					nonce := []uint64{233429, 19}[j]
					value := []string{"1200000000000000000000", "1800000000000000000000"}[j]
					transfer, err := types.SignTx(types.NewTransaction(nonce, owners[1], decimal(t, value), 21000, big.NewInt(2000000000), nil), types.LatestSigner(f.chain.Config()), sponsor.key)
					requireNoError(t, err)
					requireNoError(t, pool.AddLocal(transfer))
					transfers = append(transfers, transfer)
				}
			}
			recordFundingInventory(t, root, "preflight-"+role, f, append([]common.Address{f.owner}, owners[:]...), saved)
		}) {
			t.Fatal("retained funded-gap preflight failed")
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-plan.json"), map[string]interface{}{"Source": head.Header(), "Transfers": transfers, "Saved": saved}))
	var nodes [2]*rehearsalNode
	for i, role := range []string{"producer", "verifier"} {
		nodes[i] = startRehearsalNodeWithTimeout(t, seedFullStateRecoveryNode(t, filepath.Join(root, role), cleanup, byte(i+2)), 9*time.Minute)
		requireRehearsalHead(t, nodes[i].status(t), head)
		actual := readPeerPurchase(t, nodes[i])
		data, err := saved[i].MarshalBinary()
		requireNoError(t, err)
		if actual.Nonce != []uint64{18, 7}[i] || !bytes.Equal(actual.Saved, data) || len(actual.Pending)+len(actual.Queued) != 0 {
			t.Fatal("live services did not preserve the cold nonce and signed intent")
		}
	}
	encoded, err := os.ReadFile(filepath.Join(root, "isolated-verifier.rlp"))
	requireNoError(t, err)
	var isolated types.Blocks
	requireNoError(t, rlp.DecodeBytes(encoded, &isolated))
	retained := make(map[common.Hash]*types.Block)
	for _, block := range isolated {
		retained[block.Hash()] = block
	}
	if len(retained) != 19 {
		t.Fatal("expected the original incomplete nineteen-block capture")
	}
	oldHead := common.HexToHash("0x6505a7b4d1dfa80ebc3ce52e993f76bd0a283d1b3318292535cf0335df1d940e")
	captureObservedBranch(t, nodes[1], oldHead, 15130080, retained)
	if len(retained) != 22 || nodes[1].status(t).Hash != expected {
		t.Fatal("hash-based capture did not recover the three post-heal blocks after rollback")
	}
	branch := retainObservedBlocks(t, filepath.Join(root, "repair-branch.rlp"), retained)
	originals := make(map[uint64]*types.Transaction)
	for _, block := range branch {
		for _, tx := range block.Transactions() {
			retainLivePurchase(t, owners[1], originals, tx)
		}
	}
	for nonce := uint64(7); nonce < 14; nonce++ {
		if originals[nonce] == nil {
			t.Fatal("capture regression is missing a predecessor")
		}
	}
	t.Log("capture regression recovered all three post-heal block bodies and all seven predecessors after rollback; canonical head unchanged")
	first, err := originals[7].MarshalBinary()
	requireNoError(t, err)
	var hash common.Hash
	requireErrorContains(t, nodes[1].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(first)), "insufficient balance")
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 5*time.Second)
	for _, tx := range append(types.Transactions{saved[0]}, transfers...) {
		data, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, nodes[0].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(data)))
		if hash != tx.Hash() {
			t.Fatal("staging changed transaction identity")
		}
	}
	for _, node := range nodes {
		startCompetingMiner(t, node)
	}
	for _, tx := range transfers {
		awaitLiveFundingTransfer(t, nodes, tx)
	}
	gap := livePurchaseGap{index: 1, nonce: 7, saved: saved[1], head: head}
	result := repairFullStateGap(t, root, nodes, owners, gap, originals, branch, false, false)
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
	result.Final = final.Hash()
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "live-result.json"), result))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped))
	if result.FundingFailure != "" {
		t.Fatalf("funded continuation remains insufficient: %s", result.FundingFailure)
	}
	t.Logf("funded complete-state live repair completed: originals=%d successors=%d final=%d %s; separate cold audit required", result.OriginalsIncluded, result.Successors, final.NumberU64(), final.Hash().Hex())
}

func TestFullStateFundedGapColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	var plan struct{ Transfers types.Transactions }
	readHandoverJSON(t, filepath.Join(root, "funding-plan.json"), &plan)
	if len(plan.Transfers) != 2 {
		t.Fatal("two specified ordinary funding transfers required")
	}
	auditRetainedPartitionCold(t, root, plan.Transfers)
}
