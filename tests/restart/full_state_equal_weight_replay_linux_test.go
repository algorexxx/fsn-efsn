package restart

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestFullStateFreshEqualWeightRejoin(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	prepareFullStateOutage(t, root)
	installFullStateHistory(t, root)
	var diagnosis struct{ Before [2]nodeRehearsalStatus }
	readHandoverJSON(t, filepath.Join(root, "cold-sync-diagnosis.json"), &diagnosis)
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("replay-"+role, func(t *testing.T) {
			f, _, funding := openFullStateHandover(t, filepath.Join(root, role))
			for number := 4; number <= 26; number++ {
				data, err := os.ReadFile(filepath.Join(root, "original-"+role, fmt.Sprintf("block-%02d.rlp", number)))
				requireNoError(t, err)
				var block *types.Block
				requireNoError(t, rlp.DecodeBytes(data, &block))
				f.importBlock(t, block)
			}
			var original struct {
				Header *types.Header
				Owner  common.Address
				Nonce  uint64
				Saved  hexutil.Bytes
			}
			readHandoverJSON(t, filepath.Join(root, "original-"+role+".json"), &original)
			if f.chain.CurrentBlock().Hash() != diagnosis.Before[i].Hash || f.chain.CurrentBlock().Hash() != original.Header.Hash() || f.chain.GetBlockByHash(diagnosis.Before[1-i].Hash) != nil {
				t.Fatal("fresh replay differs from the original canonical branch or contains the opposite tip")
			}
			state, err := f.chain.State()
			requireNoError(t, err)
			var saved types.Transaction
			requireNoError(t, saved.UnmarshalBinary(original.Saved))
			owner, err := types.Sender(types.LatestSigner(f.chain.Config()), &saved)
			requireNoError(t, err)
			if owner != original.Owner || saved.Nonce() != original.Nonce || state.GetNonce(owner) != original.Nonce || !saved.IsBuyTicketTx() {
				t.Fatal("original saved intent does not match the reconstructed account")
			}
			key := append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
			exists, err := f.db.Has(key)
			requireNoError(t, err)
			if exists {
				t.Fatal("fresh replay unexpectedly already contains an automatic intent")
			}
			requireNoError(t, f.db.Put(key, original.Saved))
			requireNoError(t, writeStateExportJSON(filepath.Join(root, "fresh-replay-"+role+".json"), map[string]interface{}{
				"Header": f.chain.CurrentBlock().Header(), "Blocks": 26, "Saved": original.Saved,
				"OppositeHeadKnown": false, "StateReexecuted": true,
			}))
			auditFullStateHandover(t, filepath.Join(root, role), filepath.Join(root, "original-"+role), 3)
			auditFullStateParticipant(t, filepath.Join(root, "original-"+role), int(original.Header.Number.Uint64()-funding.Parent.Number.Uint64()))
		}) {
			t.Fatal("fresh equal-weight reconstruction failed")
		}
	}
	TestFullStateEqualWeightRejoin(t)
}
