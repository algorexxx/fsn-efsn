package restart

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestFullStateRetainedPartitionDisplacedAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	owner := common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")
	originals := make(map[uint64]*types.Transaction)
	locations := make(map[uint64]*types.Block)
	var head, cleanup *types.Block
	var saved []byte
	if !t.Run("cold-displaced-branch", func(t *testing.T) {
		f, _, funding := openFullStateHandover(t, filepath.Join(root, "verifier"))
		head = f.chain.CurrentBlock()
		if head.NumberU64() != 15130103 || head.Hash() != common.HexToHash("0x1a52a5d9fec08c0c5aa2adddf62dcaf115991f74919877c88e6756b771d67aaf") {
			t.Fatal("expected the stopped second partition attempt")
		}
		cleanup = f.chain.GetBlockByNumber(15130083)
		state, err := f.chain.State()
		requireNoError(t, err)
		if state.GetNonce(owner) != 7 {
			t.Fatal("expected canonical nonce 7")
		}
		saved, err = f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owner[:]...))
		requireNoError(t, err)
		var intent types.Transaction
		requireNoError(t, intent.UnmarshalBinary(saved))
		if intent.Nonce() != 14 || intent.Hash() != common.HexToHash("0x71f7c8320feac7fc0a2fcb6378cace0dd38d95a790233ab0abe42f16d5988396") {
			t.Fatal("saved nonce-14 intent changed")
		}
		for number := uint64(15130095); number <= head.NumberU64(); number++ {
			for _, hash := range rawdb.ReadAllHashes(f.db, number) {
				if hash == rawdb.ReadCanonicalHash(f.db, number) {
					continue
				}
				block := f.chain.GetBlock(hash, number)
				if block == nil {
					t.Fatal("stored noncanonical header has no block body")
				}
				for _, tx := range block.Transactions() {
					retainLivePurchase(t, owner, originals, tx)
					if originals[tx.Nonce()] != nil && originals[tx.Nonce()].Hash() == tx.Hash() {
						locations[tx.Nonce()] = block
					}
				}
			}
		}
		for nonce := uint64(7); nonce < 14; nonce++ {
			if originals[nonce] == nil || locations[nonce] == nil {
				t.Fatalf("missing stored original nonce %d", nonce)
			}
		}
		artifacts := filepath.Join(root, "audit-displaced")
		requireNoError(t, os.Mkdir(artifacts, 0700))
		block := locations[13]
		count := int(block.NumberU64() - funding.Parent.Number.Uint64())
		for block.NumberU64() > funding.Parent.Number.Uint64() {
			recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
			block = f.chain.GetBlock(block.ParentHash(), block.NumberU64()-1)
			if block == nil {
				t.Fatal("displaced branch parent is unavailable")
			}
		}
		if block.Hash() != funding.Parent.Hash() {
			t.Fatal("displaced branch does not descend from the fixture parent")
		}
		auditFullStateHandover(t, filepath.Join(root, "verifier"), artifacts, 3)
		auditFullStateParticipant(t, artifacts, count)
	}) {
		t.Fatal("displaced complete-state audit failed")
	}
	node := startRehearsalNodeWithTimeout(t, seedFullStateRecoveryNode(t, filepath.Join(root, "verifier"), cleanup, 3), 2*time.Minute)
	requireRehearsalHead(t, node.status(t), head)
	before := readPeerPurchase(t, node)
	if before.Nonce != 7 || !bytes.Equal(before.Saved, saved) || len(before.Pending)+len(before.Queued) != 0 || node.status(t).Mining || node.status(t).AutoBuy {
		t.Fatal("read-only diagnostic service started with unexpected state")
	}
	recovered := filepath.Join(root, "recovered")
	requireNoError(t, os.Mkdir(recovered, 0700))
	var records []map[string]interface{}
	for nonce := uint64(7); nonce < 14; nonce++ {
		tx := requireDisplacedPurchaseRPC(t, node, locations[nonce], originals[nonce])
		validateLiveRepairPurchase(t, node, tx)
		data, err := tx.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(filepath.Join(recovered, fmt.Sprintf("original-%d.rlp", nonce)), data, 0600))
		records = append(records, map[string]interface{}{"Nonce": nonce, "Hash": tx.Hash(), "Block": locations[nonce].Hash(), "Number": locations[nonce].NumberU64(), "Bytes": len(data)})
	}
	first, err := originals[7].MarshalBinary()
	requireNoError(t, err)
	var submitted common.Hash
	err = node.call(t, &submitted, "eth_sendRawTransaction", hexutil.Bytes(first))
	if err == nil || !strings.Contains(err.Error(), "insufficient balance") {
		t.Fatalf("expected first original to fail actual pool funding: %v", err)
	}
	after := readPeerPurchase(t, node)
	if after.Nonce != 7 || !bytes.Equal(after.Saved, saved) || len(after.Pending)+len(after.Queued) != 0 {
		t.Fatal("rejected original changed the nonce, saved intent or pool")
	}
	requireRehearsalHead(t, node.status(t), head)
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "displaced-result.json"), map[string]interface{}{"Head": head.Header(), "Owner": owner, "CanonicalNonce": after.Nonce, "Saved": hexutil.Bytes(saved), "Recovered": records, "FirstOriginalPoolError": err.Error(), "HeadAndIntentUnchanged": true, "NewFunding": false}))
	node.stop(t, false)
	t.Logf("all seven missing originals recovered through existing RPC; first correct-nonce purchase rejected for funding; canonical head, nonce and exact saved intent unchanged")
}
