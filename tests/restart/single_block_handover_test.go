package restart

import (
	"context"
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
)

func TestSingleBackupBlockHandover(t *testing.T) {
	original, successor := newHandoverFixture(t, "12020102000000000000000")
	verifier, _ := newHandoverFixture(t, "12020102000000000000000")
	parent := original.chain.CurrentBlock()
	before, err := original.chain.State()
	requireNoError(t, err)
	initialTickets, err := before.AllTickets()
	requireNoError(t, err)
	if initialTickets.NumberOfTicketsByAddress(original.owner) != 2 || initialTickets.NumberOfTicketsByAddress(successor.owner) != 0 {
		t.Fatal("expected two historical original tickets and no successor tickets")
	}
	api := ethapi.NewPublicFusionAPI(&purchaseBackend{chain: original.chain})
	end := hexutil.Uint64(ticketEnd)
	built, err := api.BuildBuyTicketSendTxArgs(context.Background(), common.BuyTicketArgs{FusionBaseArgs: common.FusionBaseArgs{From: successor.owner}, End: &end})
	requireNoError(t, err)
	purchase := successor.signPurchaseData(t, *built.Input)
	block := original.buildBlockWithTransactions(t, parent.Time()+120, []*types.Transaction{purchase})
	original.importBlock(t, block)
	verifier.importBlock(t, block)
	snapshot, err := datong.NewSnapshotFromHeader(block.Header())
	requireNoError(t, err)
	selected := initialTickets.ToMap()[snapshot.Selected]
	if selected.Owner != original.owner {
		t.Fatal("first block did not select an original ticket")
	}
	after, err := original.chain.State()
	requireNoError(t, err)
	tickets, err := after.AllTickets()
	requireNoError(t, err)
	parentHash := parent.Hash()
	firstID := crypto.Keccak256Hash(successor.owner.Bytes(), parentHash.Bytes())
	first := tickets.ToMap()[firstID]
	if tickets.NumberOfTicketsByAddress(original.owner) != 1 || tickets.NumberOfTicketsByAddress(successor.owner) != 1 || first.Owner != successor.owner || first.StartTime != parent.Time() || first.ExpireTime != ticketEnd || first.Height != block.NumberU64() {
		t.Fatal("first block did not preserve one historical original ticket and create the long successor ticket")
	}
	refundBefore := before.GetTimeLockBalance(common.SystemAssetID, original.owner).GetSpendableValue(block.Time(), selected.ExpireTime)
	refundAfter := after.GetTimeLockBalance(common.SystemAssetID, original.owner).GetSpendableValue(block.Time(), selected.ExpireTime)
	if new(big.Int).Sub(refundAfter, refundBefore).Cmp(decimal(t, "5000000000000000000000")) != 0 {
		t.Fatal("selected original ticket did not return its remaining time-lock interval")
	}
	retired, err := after.Database().OpenTrie(block.Root())
	requireNoError(t, err)
	retiredAccount, err := retired.TryGet(original.owner.Bytes())
	requireNoError(t, err)
	var remainingOriginal common.Ticket
	for _, ticket := range tickets.ToTicketSlice() {
		if ticket.Owner == original.owner {
			remainingOriginal = ticket
		}
	}
	if remainingOriginal.ExpireTime >= jumpTime {
		t.Fatal("remaining historical ticket unexpectedly valid at the present-day jump")
	}
	t.Logf("single backup block height=%d time=%d originalTickets=1 successorTickets=1 selected=%s refund=5000FSN-time-lock successorFirst=%s remainingOriginal=%s expires=%d", block.NumberU64(), block.Time(), snapshot.Selected.Hex(), firstID.Hex(), remainingOriginal.ID.Hex(), remainingOriginal.ExpireTime)
	for i := 0; i < 5; i++ {
		timestamp := successor.chain.CurrentBlock().Time() + 120
		if i == 0 {
			timestamp = jumpTime
		}
		block = successor.buildBlock(t, timestamp, true)
		successor.importBlock(t, block)
		verifier.importBlock(t, block)
		if successor.chain.CurrentBlock().Root() != verifier.chain.CurrentBlock().Root() {
			t.Fatal("independent successor execution root differs")
		}
		snapshot, err = datong.NewSnapshotFromHeader(block.Header())
		requireNoError(t, err)
		if i == 0 && snapshot.Selected != firstID {
			t.Fatal("first successor block did not select its initial long-lived ticket")
		}
		after, err = successor.chain.State()
		requireNoError(t, err)
		tickets, err = after.AllTickets()
		requireNoError(t, err)
		trie, err := after.Database().OpenTrie(block.Root())
		requireNoError(t, err)
		account, err := trie.TryGet(original.owner.Bytes())
		requireNoError(t, err)
		if string(account) != string(retiredAccount) || after.GetNonce(original.owner) != 0 {
			t.Fatal("original account changed after its sole block")
		}
		retreatedOriginal := false
		for _, id := range snapshot.Retreat {
			if id == remainingOriginal.ID {
				retreatedOriginal = true
			}
		}
		t.Logf("successor step=%d height=%d time=%d tickets=%d originalTickets=%d successorTickets=%d retreatCount=%d originalRetreated=%t root=%s", i+1, block.NumberU64(), block.Time(), tickets.NumberOfTickets(), tickets.NumberOfTicketsByAddress(original.owner), tickets.NumberOfTicketsByAddress(successor.owner), len(snapshot.Retreat), retreatedOriginal, block.Root().Hex())
	}
	if tickets.NumberOfTickets() != 1 || tickets.NumberOfTicketsByAddress(original.owner) != 0 || tickets.NumberOfTicketsByAddress(successor.owner) != 1 || after.GetNonce(successor.owner) != 6 {
		t.Fatal("successor did not continue alone or historical tickets were not removed")
	}
	t.Log("one original signature and no original purchases; five successor blocks; original account unchanged after initial selection refund, with no second-ticket refund")
}

func TestSingleBackupBlockRejectsShortSuccessorTicket(t *testing.T) {
	original, successor := newHandoverFixture(t, "12020102000000000000000")
	parent := original.chain.CurrentBlock()
	purchase := successor.signPurchase(t, parent.Time(), parent.Time()+30*24*3600)
	original.importBlock(t, original.buildBlockWithTransactions(t, parent.Time()+120, []*types.Transaction{purchase}))
	historicalHead := successor.chain.CurrentBlock().Hash()
	block := successor.buildBlock(t, jumpTime, true)

	_, err := successor.chain.InsertChain(types.Blocks{block})

	requireErrorContains(t, err, "checkTicketInfo ticket ExpireTime mismatch")
	if successor.chain.CurrentBlock().Hash() != historicalHead {
		t.Fatal("expired successor ticket advanced canonical head")
	}
}
