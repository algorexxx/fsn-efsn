package restart

import (
	"math/big"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/core/types"
)

func TestSingleRemainingTicketRequiresReplacement(t *testing.T) {
	f := newFixture(t)
	expected := "Next block doesn't have ticket, wait buy ticket"
	for i := 0; i < 4; i++ {
		timestamp := f.chain.CurrentBlock().Time() + 120
		if i == 2 {
			timestamp = jumpTime
		}
		f.importBlock(t, f.buildBlock(t, timestamp, i > 0))
	}
	parent := f.chain.CurrentBlock()
	header := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number(), big.NewInt(1)), Coinbase: f.owner, Time: parent.Time() + 120, Difficulty: new(big.Int)}
	requireNoError(t, f.engine.Prepare(f.chain, header))
	statedb, err := f.chain.State()
	requireNoError(t, err)

	_, err = f.engine.Finalize(f.chain, header, statedb, nil, nil, nil)

	if err == nil || !strings.Contains(err.Error(), expected) {
		t.Fatalf("expected %q, got %v", expected, err)
	}
}
