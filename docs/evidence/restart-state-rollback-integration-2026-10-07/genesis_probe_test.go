package recovery

import (
	"testing"

	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/params"
)

func TestF11DeclaredGenesisIdentity(t *testing.T) {
	want := params.MainnetGenesisHash

	block := core.DefaultGenesisBlock().ToBlock(nil)

	t.Logf("declared=%s built=%s state=%s", want.Hex(), block.Hash().Hex(), block.Root().Hex())
	if block.Hash() != want {
		t.Fatal("current genesis construction does not reproduce declared mainnet identity")
	}
}
