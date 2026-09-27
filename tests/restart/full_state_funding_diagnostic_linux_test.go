package restart

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestFullStateFundingLedger(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_FUNDING_DIAGNOSIS")
	if root == "" {
		t.Skip("requires retained cold funding-continuation artifacts")
	}
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	var saved [2]struct{ Header *types.Header }
	for i, role := range []string{"producer", "verifier"} {
		readHandoverJSON(t, filepath.Join(root, "diagnostic-saved-"+role+".json"), &saved[i])
	}
	if saved[0].Header.Hash() != saved[1].Header.Hash() {
		t.Fatal("retained cold diagnosis heads differ")
	}
	var recovery struct {
		Final         *types.Header
		Contributions types.Transactions
	}
	readHandoverJSON(t, filepath.Join(root, "funding-recovery.json"), &recovery)
	if len(recovery.Contributions) != 2 {
		t.Fatal("expected two specified contributions")
	}
	count := int(saved[0].Header.Number.Uint64()-recovery.Final.Number.Uint64()) + 18
	artifacts := filepath.Join(root, "diagnostic-blocks")
	var last fullStateBlockLedger
	readHandoverJSON(t, filepath.Join(artifacts, fmt.Sprintf("block-%02d.json", count)), &last)
	if last.Header.Hash() != saved[0].Header.Hash() {
		t.Fatal("retained ledger does not end at the diagnosed canonical head")
	}
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	allowed := make(map[common.Hash]uint64)
	for _, tx := range recovery.Contributions {
		allowed[tx.Hash()] = recovery.Final.Number.Uint64() - 1
	}
	auditFullStateParticipantTransfers(t, artifacts, count, allowed)
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-ledger.json"), map[string]interface{}{"Final": last.Header, "Blocks": count, "LedgerPassed": true, "LiveContinuationPassed": false}))
	t.Log("complete-state funding ledger passed from retained cold artifacts, including independently checked automatic mature-lock conversion; live continuation remains failed")
}

func TestFullStateFundingColdDiagnosis(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_FUNDING_DIAGNOSIS")
	if root == "" {
		t.Skip("requires stopped disposable funding-continuation databases")
	}
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	owners := [2]common.Address{common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"), common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")}
	var saved [2]*types.Transaction
	var final *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("saved-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			head := f.chain.CurrentBlock()
			if final != nil && head.Hash() != final.Hash() {
				t.Fatal("stopped funding continuation heads differ")
			}
			final = head
			data, err := f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owners[i][:]...))
			requireNoError(t, err)
			saved[i] = new(types.Transaction)
			requireNoError(t, saved[i].UnmarshalBinary(data))
			sender, err := types.Sender(types.LatestSigner(f.chain.Config()), saved[i])
			requireNoError(t, err)
			state, err := f.chain.State()
			requireNoError(t, err)
			if sender != owners[i] || !saved[i].IsBuyTicketTx() || saved[i].Nonce() != state.GetNonce(sender) {
				t.Fatal("cold pending purchase has a different owner, intent or canonical nonce")
			}
			requireNoError(t, writeStateExportJSON(filepath.Join(root, "diagnostic-saved-"+role+".json"), map[string]interface{}{"Header": head.Header(), "Owner": sender, "Nonce": state.GetNonce(sender), "Saved": hexutil.Bytes(data), "Transaction": saved[i]}))
		}) {
			t.Fatal("cold saved-purchase diagnosis failed")
		}
	}
	for _, role := range []string{"producer", "verifier"} {
		if !t.Run("pool-"+role, func(t *testing.T) {
			f, _, _ := openFullStateHandover(t, filepath.Join(root, role))
			pool := f.newPool(t)
			for _, tx := range saved {
				requireNoError(t, pool.AddLocal(tx))
			}
			recordFundingInventory(t, root, role+"-diagnostic", f, append([]common.Address{f.owner}, owners[:]...), saved)
			t.Logf("cold funding diagnosis role=%s accepted both saved purchases nonce=%d/%d hashes=%s/%s at common head=%d %s; no signing, rebroadcast or nonce repair", role, saved[0].Nonce(), saved[1].Nonce(), saved[0].Hash().Hex(), saved[1].Hash().Hex(), final.NumberU64(), final.Hash().Hex())
		}) {
			t.Fatal("cold purchase admission failed")
		}
	}
	artifacts := filepath.Join(root, "diagnostic-blocks")
	count := captureFullStateColdSuffixAt(t, root, final, artifacts)
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	var recovery struct {
		Final         *types.Header
		Contributions types.Transactions
	}
	readHandoverJSON(t, filepath.Join(root, "funding-recovery.json"), &recovery)
	if len(recovery.Contributions) != 2 {
		t.Fatal("expected two specified funding transfers")
	}
	allowed := make(map[common.Hash]uint64)
	for _, tx := range recovery.Contributions {
		allowed[tx.Hash()] = recovery.Final.Number.Uint64() - 1
	}
	auditFullStateParticipantTransfers(t, artifacts, count, allowed)
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-diagnosis.json"), map[string]interface{}{"Final": final.Header(), "Blocks": count, "SavedPurchases": saved, "BothColdPoolsAccepted": true, "BothCanonicalNoncesMatch": true, "LiveContinuationPassed": false}))
	t.Log("cold funding-continuation diagnosis passed: canonical account ledgers match, both correct-nonce purchases admitted on both cold nodes; remote live pool contents and the exact delivery failure were not sampled")
}
