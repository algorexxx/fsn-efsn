package restart

import (
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/p2p"
)

func TestFullStatePartitionColdDiagnosis(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_PARTITION_DIAGNOSIS")
	if root == "" {
		t.Skip("requires stopped disposable complete-state partition copies")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and isolated node rehearsal required")
	}
	var heads [2]*types.Block
	var cleanup *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("audit-"+role, func(t *testing.T) {
			directory := filepath.Join(root, role)
			f, _, funding := openFullStateHandover(t, directory)
			head := f.chain.CurrentBlock()
			heads[i] = head
			anchor := f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			if anchor == nil || (cleanup != nil && anchor.Hash() != cleanup.Hash()) {
				t.Fatal("missing or different shared cleanup anchor")
			}
			cleanup = anchor
			if rawdb.ReadHeadBlockHash(f.db) != head.Hash() || rawdb.ReadHeadHeaderHash(f.db) != head.Hash() || rawdb.ReadHeadFastBlockHash(f.db) != head.Hash() {
				t.Fatal("cold partition head markers differ")
			}
			artifacts := filepath.Join(root, "cold-"+role)
			requireNoError(t, os.Mkdir(artifacts, 0700))
			count := int(head.NumberU64() - funding.Parent.Number.Uint64())
			for n := funding.Parent.Number.Uint64() + 1; n <= head.NumberU64(); n++ {
				block := f.chain.GetBlockByNumber(n)
				if block == nil {
					t.Fatal("missing cold canonical block")
				}
				recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
			}
			auditFullStateHandover(t, directory, artifacts, 3)
			auditFullStateParticipant(t, artifacts, count)
			owner := common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF")
			if i == 1 {
				owner = common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")
			}
			state, err := f.chain.State()
			requireNoError(t, err)
			saved, err := f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owner[:]...))
			requireNoError(t, err)
			td := f.chain.GetTd(head.Hash(), head.NumberU64())
			requireNoError(t, writeStateExportJSON(filepath.Join(root, "cold-"+role+".json"), map[string]interface{}{"Header": head.Header(), "TotalDifficulty": td.String(), "Owner": owner, "Nonce": state.GetNonce(owner), "Saved": hexutil.Bytes(saved)}))
			t.Logf("partition cold audit role=%s blocks=%d head=%d %s td=%s nonce=%d saved-bytes=%d", role, count, head.NumberU64(), head.Hash().Hex(), td, state.GetNonce(owner), len(saved))
		}) {
			t.Fatal("cold branch audit failed; synchronization diagnosis not started")
		}
	}
	if heads[0].Hash() == heads[1].Hash() {
		t.Fatal("diagnosis requires two different stopped branches")
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), cleanup, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), cleanup, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNode(t, paths[0]), startRehearsalNode(t, paths[1])}
	before := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	for i, node := range nodes {
		requireRehearsalHead(t, node.status(t), heads[i])
	}
	ids := [2]string{connectRehearsalPeer(t, nodes[0], nodes[1]), connectRehearsalPeer(t, nodes[1], nodes[0])}
	started := time.Now()
	for time.Since(started) < 45*time.Second {
		for _, node := range nodes {
			status := node.status(t)
			if status.Mining || status.AutoBuy || status.Signatures != 0 {
				t.Fatal("cold diagnostic unexpectedly enabled signing or buying")
			}
		}
		if nodes[0].status(t).Hash == nodes[1].status(t).Hash {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}
	automatic := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	var peers [2][]*p2p.PeerInfo
	for i, node := range nodes {
		requireNoError(t, node.call(t, &peers[i], "admin_peers"))
	}
	t.Logf("partition cold automatic sync elapsed=%s matched=%t td=%s/%s peers=%d/%d", time.Since(started), automatic[0].Hash == automatic[1].Hash, (*big.Int)(automatic[0].TD), (*big.Int)(automatic[1].TD), len(peers[0]), len(peers[1]))
	forced := "not attempted"
	if automatic[0].Hash != automatic[1].Hash {
		local := 0
		if (*big.Int)(automatic[0].TD).Cmp((*big.Int)(automatic[1].TD)) > 0 {
			local = 1
		}
		remote := automatic[1-local]
		err := nodes[local].call(t, nil, "lab_sync", ids[local], remote.Hash, remote.TD)
		forced = "success"
		if err != nil {
			forced = err.Error()
		}
		t.Logf("partition diagnostic explicit downloader node=%d target=%s result=%s", local+1, remote.Hash.Hex(), forced)
	}
	after := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "cold-sync-diagnosis.json"), map[string]interface{}{"Before": before, "Automatic": automatic, "Peers": peers, "ExplicitDownloader": forced, "After": after}))
	for _, node := range nodes {
		node.stop(t, false)
	}
	if automatic[0].Hash != automatic[1].Hash {
		t.Fatal("stopped fork did not converge through ordinary synchronization; diagnostic retained")
	}
}
