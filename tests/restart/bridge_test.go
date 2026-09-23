package restart

import (
	"math/big"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestPresentDaySuccessorRejectsExpiredTicket(t *testing.T) {
	f := newFixture(t)
	expected := "checkTicketInfo ticket ExpireTime mismatch"
	built := f.buildBlock(t, jumpTime, false)
	encoded, err := rlp.EncodeToBytes(built)
	requireNoError(t, err)
	var received types.Block
	requireNoError(t, rlp.DecodeBytes(encoded, &received))

	_, err = f.chain.InsertChain(types.Blocks{&received})

	if err == nil || !strings.Contains(err.Error(), expected) {
		t.Fatalf("expected %q, got %v", expected, err)
	}
}

func TestHistoricalBridgeImportsOnIndependentState(t *testing.T) {
	producer := newFixture(t)
	verifier := newFixture(t)
	expectedCoverage := decimal(t, "5000000000000000000000")
	for i := 0; i < 8; i++ {
		timestamp := producer.chain.CurrentBlock().Time() + 120
		if i == 2 {
			timestamp = jumpTime
		}
		built := producer.buildBlock(t, timestamp, i > 0)
		producer.importBlock(t, built)
		verifier.importBlock(t, built)
		statedb, err := verifier.chain.State()
		requireNoError(t, err)
		tickets, err := statedb.AllTickets()
		requireNoError(t, err)
		t.Logf("step=%d height=%d time=%d tickets=%d owned=%d liquid=%s", i+1, built.NumberU64(), built.Time(), tickets.NumberOfTickets(), tickets.NumberOfTicketsByAddress(verifier.owner), statedb.GetBalance(common.SystemAssetID, verifier.owner))
		if i == 0 {
			coverage := statedb.GetTimeLockBalance(common.SystemAssetID, verifier.owner).GetSpendableValue(built.Time(), ticketEnd)
			if coverage.Cmp(expectedCoverage) != 0 {
				t.Fatalf("first historical refund coverage: expected %s, got %s", expectedCoverage, coverage)
			}
		}
		if producer.chain.CurrentBlock().Root() != verifier.chain.CurrentBlock().Root() {
			t.Fatal("independent execution roots differ")
		}
	}
	if verifier.chain.CurrentBlock().Number().Cmp(new(big.Int).Add(verifier.parent.Number(), big.NewInt(8))) != 0 {
		t.Fatal("bridge did not reach expected height")
	}
}
