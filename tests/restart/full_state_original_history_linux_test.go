package restart

import (
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestFullStateOriginalForkHistory(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_HISTORY_RECHECK")
	if root == "" {
		t.Skip("requires original stopped partition fixture with retained head records")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" || os.Getenv("FUSION_RESTART_NODE_REHEARSAL") != "1" {
		t.Fatal("isolated disposable fixture required")
	}
	var diagnosis struct{ Before []nodeRehearsalStatus }
	readHandoverJSON(t, filepath.Join(root, "cold-sync-diagnosis.json"), &diagnosis)
	if len(diagnosis.Before) != 2 || diagnosis.Before[0].Hash == diagnosis.Before[1].Hash || (*big.Int)(diagnosis.Before[0].TD).Cmp((*big.Int)(diagnosis.Before[1].TD)) != 0 {
		t.Fatal("expected original different heads at equal total difficulty")
	}
	installFullStateHistory(t, root)
	var anchor *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("original-head-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			if f.chain.CurrentBlock().Hash() != diagnosis.Before[i].Hash {
				t.Fatal("original stopped head was changed")
			}
			block := f.chain.GetBlockByNumber(funding.Parent.Number.Uint64() + 3)
			if block == nil || (anchor != nil && block.Hash() != anchor.Hash()) {
				t.Fatal("shared recovery anchor differs")
			}
			anchor = block
		}) {
			t.Fatal("original fixture differs")
		}
	}
	paths := [2]string{seedFullStateRecoveryNode(t, filepath.Join(root, "producer"), anchor, 2), seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), anchor, 3)}
	nodes := [2]*rehearsalNode{startRehearsalNode(t, paths[0]), startRehearsalNode(t, paths[1])}
	id := connectRehearsalPeer(t, nodes[0], nodes[1])
	before := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	for i, state := range before {
		if state.Hash != diagnosis.Before[i].Hash || state.Mining || state.AutoBuy || state.Signatures != 0 {
			t.Fatal("original no-signing diagnostic precondition differs")
		}
	}
	requireNoError(t, nodes[0].call(t, nil, "lab_sync", id, before[1].Hash, before[1].TD))
	var imported *displacedPurchaseBlock
	requireNoError(t, nodes[0].call(t, &imported, "eth_getBlockByHash", before[1].Hash, false))
	if imported == nil || imported.Hash != before[1].Hash || uint64(imported.Number) != before[1].Number {
		t.Fatal("explicit downloader did not store the remote branch")
	}
	after := [2]nodeRehearsalStatus{nodes[0].status(t), nodes[1].status(t)}
	for _, state := range after {
		if state.Mining || state.AutoBuy || state.Signatures != 0 || state.Hash == (common.Hash{}) {
			t.Fatal("history recheck enabled signing or buying")
		}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "history-recheck.json"), map[string]interface{}{"Before": before, "After": after, "RemoteStored": imported.Hash}))
	for _, node := range nodes {
		node.stop(t, false)
	}
	t.Logf("original fork ancestry recheck passed: explicit downloader stored remote=%s at height=%d with no signing; final heads=%s/%s", imported.Hash.Hex(), imported.Number, after[0].Hash.Hex(), after[1].Hash.Hex())
}
