package restart

import (
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestHandoverMissingRecoveryPurchase(t *testing.T) {
	for _, omit := range []string{"jump", "cleanup"} {
		t.Run(omit, func(t *testing.T) {
			original, successor := newHandoverFixture(t, "12020102000000000000000")
			verifier, _ := newHandoverFixture(t, "12020102000000000000000")
			parent := original.chain.CurrentBlock()
			purchase := successor.signPurchase(t, parent.Time(), ticketEnd)
			first := original.buildBlockWithTransactions(t, parent.Time()+120, []*types.Transaction{purchase})
			original.importBlock(t, first)
			verifier.importBlock(t, first)
			jump := successor.buildBlock(t, jumpTime, omit != "jump")
			successor.importBlock(t, jump)
			verifier.importBlock(t, jump)
			if omit == "cleanup" {
				parent = successor.chain.CurrentBlock()
				header := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number(), big.NewInt(1)), Time: jumpTime + 120, Coinbase: successor.owner, Difficulty: new(big.Int)}
				requireNoError(t, successor.engine.Prepare(successor.chain, header))
				s, err := successor.chain.State()
				requireNoError(t, err)
				_, err = successor.engine.Finalize(successor.chain, header, s, nil, nil, nil)
				requireErrorContains(t, err, "Next block have no ticket")
				if successor.chain.CurrentBlock().Hash() != parent.Hash() {
					t.Fatal("rejected empty cleanup changed canonical head")
				}
				cleanup := successor.buildBlock(t, jumpTime+120, true)
				successor.importBlock(t, cleanup)
				verifier.importBlock(t, cleanup)
				t.Log("cleanup without replacement is rejected before signing; adding the purchase resumes production")
				return
			}
			parent = successor.chain.CurrentBlock()
			s, err := successor.chain.State()
			requireNoError(t, err)
			tickets, err := s.AllTickets()
			requireNoError(t, err)
			if tickets.NumberOfTicketsByAddress(successor.owner) != 0 {
				t.Fatal("missing recovery purchase did not consume the final usable ticket")
			}
			for _, ticket := range tickets.ToTicketSlice() {
				if ticket.ExpireTime >= parent.Time() {
					t.Fatal("another usable ticket survived the omitted jump purchase")
				}
			}
			if tickets.NumberOfTickets() <= 1 {
				t.Fatal("counterexample must retain multiple expired tickets")
			}
			header := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number(), big.NewInt(1)), Time: parent.Time() + 120, Coinbase: successor.owner, Difficulty: new(big.Int)}

			err = successor.engine.Prepare(successor.chain, header)

			if err != datong.ErrNoTicket {
				t.Fatalf("expected stranded successor, got %v", err)
			}
			t.Logf("accepted %s block without replacement at height=%d leaves storedTickets=%d successorTickets=0; next preparation fails with no ticket", omit, parent.NumberU64(), tickets.NumberOfTickets())
		})
	}
}
