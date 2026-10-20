package restart

import (
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func newHandoverFixture(t *testing.T, funding string) (*fixture, *fixture) {
	t.Helper()
	f := newFixture(t)
	keyBytes := make([]byte, 32)
	keyBytes[31] = 2
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	s, err := f.chain.State()
	requireNoError(t, err)
	if s.Exist(owner) {
		t.Fatal("synthetic successor account collision")
	}
	s.SetBalance(owner, common.SystemAssetID, decimal(t, funding))
	header := f.parent.Header()
	header.Root, err = s.Commit(true)
	requireNoError(t, err)
	requireNoError(t, s.Database().TrieDB().Commit(header.Root, false, nil))
	f.chain.Stop()
	f.parent = types.NewBlockWithHeader(header)
	rawdb.WriteBlock(f.db, f.parent)
	rawdb.WriteTd(f.db, f.parent.Hash(), f.parent.NumberU64(), big.NewInt(1))
	rawdb.WriteCanonicalHash(f.db, f.parent.Hash(), f.parent.NumberU64())
	rawdb.WriteHeadBlockHash(f.db, f.parent.Hash())
	rawdb.WriteHeadHeaderHash(f.db, f.parent.Hash())
	rawdb.WriteHeadFastBlockHash(f.db, f.parent.Hash())
	config := f.chain.Config()
	f.engine = datong.New(config.DaTong, f.db)
	f.chain, err = core.NewBlockChain(f.db, &core.CacheConfig{TrieDirtyDisabled: true}, config, f.engine, vm.Config{}, nil)
	requireNoError(t, err)
	successor := *f
	successor.key, successor.owner = key, owner
	return f, &successor
}
