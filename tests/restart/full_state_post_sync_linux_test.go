package restart

import (
	"bytes"
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

func TestFullStatePostSyncAccounting(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_POST_SYNC")
	if root == "" {
		t.Skip("requires stopped disposable databases after partition diagnosis")
	}
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	var diagnosis struct{ After []nodeRehearsalStatus }
	readHandoverJSON(t, filepath.Join(root, "cold-sync-diagnosis.json"), &diagnosis)
	if len(diagnosis.After) != 2 || diagnosis.After[0].Hash != diagnosis.After[1].Hash {
		t.Fatal("ordinary synchronization has not reached a common head")
	}
	var final *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("funds-"+role, func(t *testing.T) {
			directory := filepath.Join(root, role)
			requireFullStateCopy(t, directory)
			f, _, _ := openFullStateHandover(t, directory)
			final = f.chain.CurrentBlock()
			if final.Hash() != diagnosis.After[i].Hash {
				t.Fatal("cold head differs from successful synchronization")
			}
			owner := common.HexToAddress("0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF")
			if i == 1 {
				owner = common.HexToAddress("0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69")
			}
			var before struct{ Saved hexutil.Bytes }
			readHandoverJSON(t, filepath.Join(root, "cold-"+role+".json"), &before)
			saved, err := f.db.Get(append([]byte("fsn-auto-ticket-v1-"), owner[:]...))
			requireNoError(t, err)
			if !bytes.Equal(saved, before.Saved) {
				t.Fatal("synchronization changed saved purchase bytes")
			}
			var tx types.Transaction
			requireNoError(t, tx.UnmarshalBinary(saved))
			sender, err := types.Sender(types.LatestSigner(f.chain.Config()), &tx)
			requireNoError(t, err)
			if sender != owner || !tx.IsBuyTicketTx() {
				t.Fatal("saved record is not this owner's signed purchase")
			}
			var envelope common.FSNCallParam
			var purchase common.BuyTicketParam
			requireNoError(t, rlp.DecodeBytes(tx.Data(), &envelope))
			requireNoError(t, rlp.DecodeBytes(envelope.Data, &purchase))
			requireNoError(t, purchase.Check(final.Number(), final.Time()))
			state, err := f.chain.State()
			requireNoError(t, err)
			tickets, err := state.AllTickets()
			requireNoError(t, err)
			liquid := state.GetBalance(common.SystemAssetID, owner)
			locks := state.GetTimeLockBalance(common.SystemAssetID, owner)
			now := uint64(time.Now().Unix())
			coverage := locks.GetSpendableValue(common.MaxUint64(purchase.Start, now), purchase.End)
			headCoverage := locks.GetSpendableValue(common.MaxUint64(purchase.Start, final.Time()), purchase.End)
			gas := new(big.Int).Mul(new(big.Int).SetUint64(tx.Gas()), tx.GasPrice())
			need := new(big.Int).Set(gas)
			if coverage.Cmp(common.TicketPrice(final.Number())) < 0 {
				need.Add(need, common.TicketPrice(final.Number()))
			}
			pool := f.newPool(t)
			admission := "accepted"
			if err := pool.AddLocal(&tx); err != nil {
				admission = err.Error()
			}
			if tx.Nonce() == state.GetNonce(owner) && liquid.Cmp(need) < 0 && !strings.Contains(admission, "insufficient balance") {
				t.Fatalf("pool admission disagrees with insufficient interval/liquid funds: %s", admission)
			}
			requireNoError(t, writeStateExportJSON(filepath.Join(root, "post-sync-"+role+".json"), map[string]interface{}{"Header": final.Header(), "Owner": owner, "Nonce": state.GetNonce(owner), "SavedNonce": tx.Nonce(), "SavedHash": tx.Hash(), "Saved": hexutil.Bytes(saved), "LiquidWei": liquid.String(), "TimeLocks": locks, "Tickets": tickets.ToMap(), "OwnerTickets": tickets.NumberOfTicketsByAddress(owner), "Purchase": purchase, "ObservedTime": now, "CoverageAtHeadWei": headCoverage.String(), "CoverageNowWei": coverage.String(), "GasBudgetWei": gas.String(), "RequiredLiquidWei": need.String(), "PoolAdmission": admission}))
			t.Logf("post-sync funds role=%s head=%d %s nonce=%d saved-nonce=%d saved-bytes=%d tickets=%d liquid-wei=%s coverage-head-wei=%s coverage-now-wei=%s required-liquid-wei=%s pool=%s", role, final.NumberU64(), final.Hash().Hex(), state.GetNonce(owner), tx.Nonce(), len(saved), tickets.NumberOfTicketsByAddress(owner), liquid, headCoverage, coverage, need, admission)
		}) {
			t.Fatal("post-sync funding check failed")
		}
	}
	count := captureFullStateColdSuffix(t, root, final)
	auditFullStateHandover(t, filepath.Join(root, "producer"), filepath.Join(root, "blocks"), 3)
	auditFullStateParticipant(t, filepath.Join(root, "blocks"), count)
	t.Logf("post-sync complete-state accounting passed: blocks=%d head=%d %s root=%s; both cold canonical databases agree and saved records are unchanged", count, final.NumberU64(), final.Hash().Hex(), final.Root().Hex())
}
