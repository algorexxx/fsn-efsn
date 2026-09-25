package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func seedTwoMinerPeer(t *testing.T) (string, *fixture, *fixture) {
	t.Helper()
	path, first := seedPurchasePeer(t)
	second := *first
	keyBytes := make([]byte, 32)
	keyBytes[31] = 2
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	second.key, second.owner = key, crypto.PubkeyToAddress(key.PublicKey)
	s, err := first.chain.State()
	requireNoError(t, err)
	tickets, err := s.AllTickets()
	requireNoError(t, err)
	oldTickets := tickets.ToTicketSlice()
	for i, owner := range []common.Address{first.owner, second.owner} {
		s.SetBalance(owner, common.SystemAssetID, decimal(t, "1000000000000000000000000"))
		requireNoError(t, s.AddTicket(common.Ticket{Owner: owner, TicketBody: common.TicketBody{
			ID: crypto.Keccak256Hash([]byte("public two-miner fixture"), []byte{byte(i + 1)}), Height: first.parent.NumberU64() - 100,
			StartTime: first.parent.Time(), ExpireTime: common.TimeLockForever,
		}}))
	}
	for _, ticket := range oldTickets {
		requireNoError(t, s.RemoveTicket(ticket.ID))
	}
	remaining, err := s.AllTickets()
	requireNoError(t, err)
	if remaining.NumberOfTickets() != 2 || remaining.NumberOfTicketsByAddress(first.owner) != 1 || remaining.NumberOfTicketsByAddress(second.owner) != 1 {
		t.Fatal("two-owner fixture must start with exactly its two synthetic tickets")
	}
	header := first.parent.Header()
	header.MixDigest, err = s.UpdateTickets(header.Number, header.Time)
	requireNoError(t, err)
	header.Root, err = s.Commit(true)
	requireNoError(t, err)
	requireNoError(t, s.Database().TrieDB().Commit(header.Root, false, nil))
	first.chain.Stop()
	first.parent = types.NewBlockWithHeader(header)
	rawdb.WriteBlock(first.db, first.parent)
	rawdb.WriteTd(first.db, first.parent.Hash(), first.parent.NumberU64(), big.NewInt(1))
	rawdb.WriteCanonicalHash(first.db, first.parent.Hash(), first.parent.NumberU64())
	rawdb.WriteHeadBlockHash(first.db, first.parent.Hash())
	rawdb.WriteHeadHeaderHash(first.db, first.parent.Hash())
	rawdb.WriteHeadFastBlockHash(first.db, first.parent.Hash())
	config := first.chain.Config()
	first.engine = datong.New(config.DaTong, first.db)
	first.chain, err = core.NewBlockChain(first.db, &core.CacheConfig{TrieDirtyDisabled: true}, config, first.engine, vm.Config{}, nil)
	requireNoError(t, err)
	second.chain, second.engine, second.parent = first.chain, first.engine, first.parent
	return path, first, &second
}

func advanceTwoMinerFixture(t *testing.T, first, second, verifier *fixture) {
	t.Helper()
	jump := uint64(time.Now().Unix()) - 3600
	for i := 0; i < 14; i++ {
		parent := first.chain.CurrentBlock()
		timestamp := parent.Time() + 120
		if i == 2 {
			timestamp = jump
		}
		txs := []*types.Transaction{first.signPurchase(t, parent.Time(), common.TimeLockForever), second.signPurchase(t, parent.Time(), common.TimeLockForever)}
		producer := first
		if i%2 != 0 {
			producer = second
		}
		block := producer.buildBlockWithTransactions(t, timestamp, txs)
		first.importBlock(t, block)
		verifier.importBlock(t, block)
	}
}

func closeTwoMinerSeed(t *testing.T, path string, f *fixture, anchor *types.Block, key byte) {
	t.Helper()
	closeRehearsalSeed(t, path, f, anchor)
	var config nodeRehearsalConfig
	readHandoverJSON(t, filepath.Join(path, "lab.json"), &config)
	config.TestKey = key
	data, err := json.MarshalIndent(config, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(filepath.Join(path, "lab.json"), data, 0600))
}
