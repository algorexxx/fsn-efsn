package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/p2p"
)

type equalWeightObservation struct {
	Phase       string
	ObservedUTC time.Time
	Nodes       [2]nodeRehearsalStatus
	Peers       [2][]*p2p.PeerInfo
	Purchases   [2]peerPurchaseState
}

func TestFullStateEqualWeightRejoin(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	anchor, original := prepareEqualWeightRejoin(t, root)
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 10*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 10*time.Minute)}
	trace, err := os.OpenFile(filepath.Join(root, "equal-weight.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	observe := func(phase string) equalWeightObservation {
		row := equalWeightObservation{Phase: phase, ObservedUTC: time.Now().UTC()}
		for i, node := range nodes {
			row.Nodes[i] = node.status(t)
			row.Purchases[i] = readPeerPurchase(t, node)
			requireNoError(t, node.call(t, &row.Peers[i], "admin_peers"))
		}
		requireNoError(t, json.NewEncoder(trace).Encode(row))
		return row
	}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 10*time.Second)
	idleStart := time.Now()
	for time.Since(idleStart) < 45*time.Second {
		row := observe("idle-equal-weight")
		for i, status := range row.Nodes {
			requireRehearsalHead(t, status, original[i])
			if status.Mining || status.AutoBuy || len(row.Peers[i]) != 1 {
				t.Fatal("idle equal-weight control requires two connected non-mining services")
			}
		}
		time.Sleep(time.Second)
	}
	t.Logf("connected equal-weight heads remained separate for %s at %d: %s / %s", time.Since(idleStart), original[0].NumberU64(), original[0].Hash().Hex(), original[1].Hash().Hex())
	started := time.Now()
	for _, node := range nodes {
		startCompetingMiner(t, node)
	}
	firstCommon := uint64(0)
	converged := false
	for time.Since(started) < 150*time.Second {
		requireContinuousMiners(t, nodes[0], nodes[1])
		row := observe("both-mining")
		height := row.Nodes[0].Number
		if row.Nodes[1].Number < height {
			height = row.Nodes[1].Number
		}
		if height > original[0].NumberU64()+1 {
			left := readRecoveryNodeBlock(t, nodes[0], height-1)
			right := readRecoveryNodeBlock(t, nodes[1], height-1)
			if left.Hash() == right.Hash() {
				if firstCommon == 0 {
					firstCommon = height - 1
					t.Logf("ordinary live sync first common descendant=%d %s after %s", firstCommon, left.Hash().Hex(), time.Since(started))
				}
				if height-1 >= firstCommon+3 {
					converged = true
					break
				}
			}
		}
		time.Sleep(time.Second)
	}
	elapsed := time.Since(started)
	live := observe("live-end")
	for _, node := range nodes {
		stopPeerAutoMiner(t, node)
	}
	if converged {
		awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	}
	stopped := observe("stopped")
	for _, node := range nodes {
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped.Purchases))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "equal-weight-result.json"), map[string]interface{}{
		"Converged": converged, "FirstCommon": firstCommon, "LiveElapsedSeconds": elapsed.Seconds(),
		"Live": live, "Stopped": stopped, "ForcedSync": false, "NewFunding": false,
	}))
	if !converged {
		t.Fatal("equal-weight live branches did not converge and advance three common descendants within 150 seconds; retain both cold ledgers")
	}
	t.Logf("equal-weight live rejoin passed without forced sync or new funding: live=%s final=%d %s", elapsed, stopped.Nodes[0].Number, stopped.Nodes[0].Hash.Hex())
}

func prepareEqualWeightRejoin(t *testing.T, root string) (*types.Block, [2]*types.Block) {
	t.Helper()
	var expected struct{ Before [2]nodeRehearsalStatus }
	readHandoverJSON(t, filepath.Join(root, "cold-sync-diagnosis.json"), &expected)
	if expected.Before[0].Hash == expected.Before[1].Hash || expected.Before[0].Number != expected.Before[1].Number || (*big.Int)(expected.Before[0].TD).Cmp((*big.Int)(expected.Before[1].TD)) != 0 {
		t.Fatal("source must be the retained equal-height, equal-weight split")
	}
	var anchor *types.Block
	var heads [2]*types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("preflight-"+role, func(t *testing.T) {
			f, source, funding := openFullStateHandover(t, filepath.Join(root, role))
			head := f.chain.CurrentBlock()
			if head.Hash() != expected.Before[i].Hash || f.chain.GetTd(head.Hash(), head.NumberU64()).Cmp((*big.Int)(expected.Before[i].TD)) != 0 {
				t.Fatal("source head or total difficulty changed")
			}
			heads[i] = head
			candidate := f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			if candidate == nil || (anchor != nil && anchor.Hash() != candidate.Hash()) {
				t.Fatal("missing shared recovery anchor")
			}
			anchor = candidate
			history := os.Getenv("FUSION_RESTART_HISTORY_INPUT")
			if !filepath.IsAbs(history) {
				t.Fatal("absolute genuine history input required")
			}
			verified := readFullStateHistory(t, history, func(block *types.Block, td *big.Int) {
				if block.NumberU64() == source.Source.Number.Uint64() {
					return
				}
				stored := f.chain.GetBlockByNumber(block.NumberU64())
				if stored == nil || stored.Hash() != block.Hash() || f.chain.GetTd(stored.Hash(), stored.NumberU64()).Cmp(td) != 0 {
					t.Fatal("genuine historical body or difficulty missing from copied database")
				}
			})
			var exported fullStateHistoryResult
			readHandoverJSON(t, history+".export.json", &exported)
			if verified != exported {
				t.Fatal("history identity differs from original export")
			}
			owners := []common.Address{f.owner, common.HexToAddress("0x2b5ad5c4795c026514f8317c7a215e218dccd6cf"), common.HexToAddress("0x6813eb9362372eef6200f3b1dbc3f819671cba69")}
			var saved [2]*types.Transaction
			for j, owner := range owners[1:] {
				key := append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
				exists, err := f.db.Has(key)
				requireNoError(t, err)
				if exists {
					data, err := f.db.Get(key)
					requireNoError(t, err)
					saved[j] = new(types.Transaction)
					requireNoError(t, saved[j].UnmarshalBinary(data))
				}
			}
			recordFundingInventory(t, root, "preflight-"+role, f, owners, saved)
			t.Logf("retained equal-weight branch verified role=%s head=%s td=%s genuine-ancestors=90000 opposite-head-already-stored=%t", role, head.Hash().Hex(), f.chain.GetTd(head.Hash(), head.NumberU64()), f.chain.GetBlockByHash(expected.Before[1-i].Hash) != nil)
		}) {
			t.Fatal("retained equal-weight preflight failed")
		}
	}
	return anchor, heads
}
