package restart

import (
	"encoding/json"
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateEqualWeightCoordinatedPause(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	anchor, original := prepareEqualWeightRejoin(t, root)
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNodeWithTimeout(t, paths[0], 10*time.Minute), startRehearsalNodeWithTimeout(t, paths[1], 10*time.Minute)}
	trace, err := os.OpenFile(filepath.Join(root, "pause.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	requireNoError(t, err)
	defer trace.Close()
	retained := [2]map[common.Hash]*types.Block{make(map[common.Hash]*types.Block), make(map[common.Hash]*types.Block)}
	base := anchor.NumberU64() - 3
	observe := func(phase string) equalWeightObservation {
		row := equalWeightObservation{Phase: phase, ObservedUTC: time.Now().UTC()}
		for i, node := range nodes {
			row.Nodes[i] = node.status(t)
			row.Purchases[i] = readPeerPurchase(t, node)
			requireNoError(t, node.call(t, &row.Peers[i], "admin_peers"))
			captureObservedBranch(t, node, row.Nodes[i].Hash, base, retained[i])
		}
		requireNoError(t, json.NewEncoder(trace).Encode(row))
		return row
	}
	connectRehearsalPeer(t, nodes[0], nodes[1])
	awaitMinerPartitionPeers(t, nodes[0], nodes[1], 1, 10*time.Second)
	initial := observe("connected-idle")
	for i, status := range initial.Nodes {
		requireRehearsalHead(t, status, original[i])
		if status.Mining || status.AutoBuy {
			t.Fatal("initial services must have mining and buying disabled")
		}
	}
	for _, node := range nodes {
		startCompetingMiner(t, node)
	}
	var before equalWeightObservation
	reproduced := false
	started := time.Now()
	for time.Since(started) < 60*time.Second {
		requireContinuousMiners(t, nodes[0], nodes[1])
		before = observe("both-mining")
		if before.Nodes[0].Hash == before.Nodes[1].Hash {
			t.Fatal("branches converged before the pause; this attempt cannot prove assisted recovery")
		}
		if before.Nodes[0].Number >= original[0].NumberU64()+2 && before.Nodes[0].Number == before.Nodes[1].Number && (*big.Int)(before.Nodes[0].TD).Cmp((*big.Int)(before.Nodes[1].TD)) == 0 {
			reproduced = true
			break
		}
		time.Sleep(time.Second)
	}
	if !reproduced {
		t.Fatal("did not reproduce an advancing equal-weight split before the pause")
	}
	for i, role := range []string{"producer", "verifier"} {
		var branch types.Blocks
		for block := retained[i][before.Nodes[i].Hash]; block != nil; block = retained[i][block.ParentHash()] {
			branch = append(branch, block)
		}
		for left, right := 0, len(branch)-1; left < right; left, right = left+1, right-1 {
			branch[left], branch[right] = branch[right], branch[left]
		}
		encoded, err := rlp.EncodeToBytes(branch)
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(root, "isolated-"+role+".rlp"), encoded, 0600))
	}
	pauseStarted := time.Now()
	stopPeerAutoMiner(t, nodes[0])
	paused := observe("pause-applied")
	t.Logf("coordinated pause applied to donation producer at heads %d/%d after reproducing distinct equal-weight descendants; entrant remains enabled", before.Nodes[0].Number, before.Nodes[1].Number)
	firstCommon := uint64(0)
	converged := false
	for time.Since(pauseStarted) < 150*time.Second {
		row := observe("donation-paused")
		if row.Nodes[0].Mining || row.Nodes[0].AutoBuy || !row.Nodes[1].Mining || !row.Nodes[1].AutoBuy || len(row.Peers[0]) != 1 || len(row.Peers[1]) != 1 {
			t.Fatal("coordinated pause requires the donation worker disabled and the entrant enabled with both services connected")
		}
		height := common.MinUint64(row.Nodes[0].Number, row.Nodes[1].Number)
		if height > before.Nodes[1].Number+1 {
			left := readRecoveryNodeBlock(t, nodes[0], height-1)
			right := readRecoveryNodeBlock(t, nodes[1], height-1)
			if left.Hash() == right.Hash() && readRecoveryNodeBlock(t, nodes[0], before.Nodes[1].Number).Hash() == before.Nodes[1].Hash {
				if firstCommon == 0 {
					firstCommon = height - 1
					t.Logf("ordinary sync adopted entrant branch after pause: first-common=%d hash=%s elapsed=%s", firstCommon, left.Hash().Hex(), time.Since(pauseStarted))
				}
				if height-1 >= firstCommon+3 {
					converged = true
					break
				}
			}
		}
		time.Sleep(time.Second)
	}
	elapsed := time.Since(pauseStarted)
	live := observe("live-end")
	stopPeerAutoMiner(t, nodes[1])
	if converged {
		awaitStoppedPartitionHead(t, nodes[0], nodes[1])
	}
	stopped := observe("stopped")
	for i, node := range nodes {
		if readRecoveryNodeBlock(t, node, anchor.NumberU64()).Hash() != anchor.Hash() {
			t.Fatal("recovery anchor changed")
		}
		retainObservedBlocks(t, filepath.Join(root, fmt.Sprintf("observed-%d.rlp", i)), retained[i])
		node.stop(t, false)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "stopped-purchases.json"), stopped.Purchases))
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "pause-result.json"), map[string]interface{}{
		"Converged": converged, "FirstCommon": firstCommon, "PauseElapsedSeconds": elapsed.Seconds(),
		"BeforePause": before, "PauseApplied": paused, "Live": live, "Stopped": stopped,
		"ForcedSync": false, "NewFunding": false, "ManualRepair": false, "PausedProducer": "donation",
	}))
	if !converged {
		t.Fatal("coordinated pause did not produce ordinary convergence and three common descendants within 150 seconds; retain cold evidence")
	}
	t.Logf("coordinated pause convergence passed after %s, final=%d %s; saved intent recovery is assessed separately", elapsed, stopped.Nodes[0].Number, stopped.Nodes[0].Hash.Hex())
}
