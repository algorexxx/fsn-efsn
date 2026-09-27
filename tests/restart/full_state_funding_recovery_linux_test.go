package restart

import (
	"bytes"
	"math/big"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func TestFullStateFundingRecovery(t *testing.T) {
	root := os.Getenv("FUSION_RESTART_FUNDING_RECOVERY")
	if root == "" {
		t.Skip("requires two verified copies of the stopped funding-failure state")
	}
	requirePartitionNamespace(t)
	if !filepath.IsAbs(root) || os.Getenv("FUSION_RESTART_CHAINDATA") != "" {
		t.Fatal("absolute disposable root and no backup source required")
	}
	var retained [2]struct {
		Header *types.Header
		Owner  common.Address
		Nonce  uint64
		Saved  hexutil.Bytes
	}
	var saved [2]*types.Transaction
	for i, role := range []string{"producer", "verifier"} {
		readHandoverJSON(t, filepath.Join(root, "source-"+role+".json"), &retained[i])
		saved[i] = new(types.Transaction)
		requireNoError(t, saved[i].UnmarshalBinary(retained[i].Saved))
	}
	expected := common.HexToHash("0x48212779e0851316084461094494cffcbb2c380362d1877a450c874913034291")
	var blocks types.Blocks
	var additional types.Transactions
	var final *types.Block
	for i, role := range []string{"producer", "verifier"} {
		if !t.Run("recover-"+role, func(t *testing.T) {
			directory := filepath.Join(root, role)
			requireFullStateCopy(t, directory)
			f, original, funding := openFullStateHandover(t, directory)
			if f.chain.CurrentBlock().Hash() != expected || retained[0].Header.Hash() != expected || retained[1].Header.Hash() != expected {
				t.Fatal("funding recovery must start at the retained failed-case canonical head")
			}
			donation := *f
			selectHandoverSuccessor(t, &donation, funding)
			entrant := *f
			key := make([]byte, 32)
			key[31] = 3
			var err error
			entrant.key, err = crypto.ToECDSA(key)
			requireNoError(t, err)
			entrant.owner = crypto.PubkeyToAddress(entrant.key.PublicKey)
			owners := []common.Address{f.owner, donation.owner, entrant.owner}
			for index, owner := range owners[1:] {
				sender, err := types.Sender(types.LatestSigner(f.chain.Config()), saved[index])
				requireNoError(t, err)
				if retained[index].Owner != owner || sender != owner || saved[index].Nonce() != retained[index].Nonce || !saved[index].IsBuyTicketTx() {
					t.Fatal("retained purchase owner, canonical nonce or intent differs")
				}
			}
			recordKey := append([]byte("fsn-auto-ticket-v1-"), retained[i].Owner[:]...)
			record, err := f.db.Get(recordKey)
			requireNoError(t, err)
			if !bytes.Equal(record, retained[i].Saved) {
				t.Fatal("source saved purchase changed before experiment")
			}
			state, err := f.chain.State()
			requireNoError(t, err)
			tickets, err := state.AllTickets()
			requireNoError(t, err)
			if state.GetNonce(donation.owner) != 7 || state.GetNonce(entrant.owner) != 11 || state.GetNonce(f.owner) != original.Nonce+2 || tickets.NumberOfTicketsByAddress(donation.owner) != 0 || tickets.NumberOfTicketsByAddress(entrant.owner) != 1 {
				t.Fatal("source nonce or ticket inventory differs from retained failure")
			}
			requireErrorContains(t, controlledPurchaseAdmission(&donation, saved[0]), "insufficient balance")
			requireNoError(t, controlledPurchaseAdmission(&entrant, saved[1]))
			recordFundingInventory(t, root, role+"-before", f, owners, saved)
			if role == "producer" {
				for index, sponsor := range []*fixture{f, &entrant} {
					value := []string{"1200000000000000000000", "1800000000000000000000"}[index]
					nonce := state.GetNonce(sponsor.owner)
					if index == 1 {
						nonce++
					}
					transfer, err := types.SignTx(types.NewTransaction(nonce, donation.owner, decimal(t, value), 21000, big.NewInt(2000000000), nil), types.LatestSigner(f.chain.Config()), sponsor.key)
					requireNoError(t, err)
					additional = append(additional, transfer)
				}
				blocks = append(blocks, entrant.buildBlockWithTransactions(t, f.chain.CurrentBlock().Time()+120, types.Transactions{saved[1], additional[0], additional[1]}))
			}
			f.importBlock(t, blocks[0])
			requireNoError(t, controlledPurchaseAdmission(&donation, saved[0]))
			recordFundingInventory(t, root, role+"-funded", f, owners, saved)
			if role == "producer" {
				blocks = append(blocks, entrant.buildBlockWithTransactions(t, f.chain.CurrentBlock().Time()+120, types.Transactions{saved[0]}))
			}
			f.importBlock(t, blocks[1])
			state, err = f.chain.State()
			requireNoError(t, err)
			tickets, err = state.AllTickets()
			requireNoError(t, err)
			if state.GetNonce(donation.owner) != 8 || state.GetNonce(entrant.owner) != 13 || state.GetNonce(f.owner) != original.Nonce+3 || tickets.NumberOfTicketsByAddress(donation.owner) != 1 {
				t.Fatal("funded purchase did not create the expected donation ticket and nonces")
			}
			after, err := f.db.Get(recordKey)
			requireNoError(t, err)
			if !bytes.Equal(after, record) {
				t.Fatal("controlled funding changed saved purchase bytes")
			}
			recordFundingInventory(t, root, role+"-recovered", f, owners, saved)
			final = f.chain.CurrentBlock()
			t.Logf("complete-state funding recovery role=%s head=%d %s donation nonce=7->8 exact-saved=%s ticket=0->1 contributions=1200+1800 FSN; entrant saved nonce 11 executed before transfer nonce 12; no saved record rewritten", role, final.NumberU64(), final.Hash().Hex(), saved[0].Hash().Hex())
		}) {
			t.Fatal("bounded existing-funds recovery failed")
		}
	}
	count := captureFullStateColdSuffix(t, root, final)
	artifacts := filepath.Join(root, "blocks")
	auditFullStateHandover(t, filepath.Join(root, "producer"), artifacts, 3)
	auditFullStateParticipant(t, artifacts, 16)
	allowed := map[common.Hash]uint64{additional[0].Hash(): blocks[0].NumberU64(), additional[1].Hash(): blocks[0].NumberU64()}
	auditFullStateParticipantTransfers(t, artifacts, count, allowed)
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-recovery.json"), map[string]interface{}{"Source": expected, "Final": final.Header(), "Contributions": additional, "SavedPurchases": saved, "Blocks": count, "LiveMiningExercised": false, "NonceGapExercised": false}))
	t.Log("complete-state existing-funds recovery passed: both cold canonical databases and every future interval reconcile; controlled inclusion only, no live repair or durable reserve claimed")
}

func recordFundingInventory(t *testing.T, root, label string, f *fixture, owners []common.Address, saved [2]*types.Transaction) {
	t.Helper()
	state, err := f.chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	accounts := make(map[common.Address]interface{})
	for _, owner := range owners {
		accounts[owner] = map[string]interface{}{"Nonce": state.GetNonce(owner), "LiquidWei": state.GetBalance(common.SystemAssetID, owner).String(), "TimeLocks": state.GetTimeLockBalance(common.SystemAssetID, owner), "TicketCount": tickets.NumberOfTicketsByAddress(owner)}
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, label+".json"), map[string]interface{}{"Header": f.chain.CurrentHeader(), "Accounts": accounts, "Tickets": tickets.ToMap(), "SavedPurchases": saved}))
}
