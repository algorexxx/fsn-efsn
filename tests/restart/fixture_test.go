package restart

import (
	"crypto/ecdsa"
	"encoding/json"
	"math/big"
	"os"
	"sort"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

const jumpTime uint64 = 1790121600
const ticketEnd uint64 = 1792713600

type fixture struct {
	db     ethdb.Database
	chain  *core.BlockChain
	engine *datong.DaTong
	key    *ecdsa.PrivateKey
	owner  common.Address
	parent *types.Block
}

type rpcObservation struct {
	ID     int
	Result json.RawMessage
}

func newFixture(t *testing.T) *fixture {
	t.Helper()
	return newFixtureWithExpiry(t, 0)
}

func newFixtureWithExpiry(t *testing.T, otherOwnerExpiry uint64) *fixture {
	t.Helper()
	values := readRPCObservations(t)
	var header types.Header
	var tickets map[common.Hash]common.TicketDisplay
	var locks common.TimeLock
	var liquid string
	requireNoError(t, json.Unmarshal(values[3], &header))
	requireNoError(t, json.Unmarshal(values[7], &tickets))
	requireNoError(t, json.Unmarshal(values[9], &liquid))
	requireNoError(t, json.Unmarshal(values[10], &locks))
	keyBytes := make([]byte, 32)
	keyBytes[31] = 1
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	originalOwner := common.HexToAddress("0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1")
	db := rawdb.NewMemoryDatabase()
	config := params.MainnetChainConfig
	genesis := &core.Genesis{Config: config, GasLimit: header.GasLimit, Difficulty: big.NewInt(1)}
	genesis.MustCommit(db)
	cache := state.NewDatabase(db)
	statedb, err := state.New(common.Hash{}, common.Hash{}, cache)
	requireNoError(t, err)
	statedb.SetBalance(owner, common.SystemAssetID, decimal(t, liquid))
	statedb.SetTimeLockBalance(owner, common.SystemAssetID, &locks)
	ids := make([]string, 0, len(tickets))
	for id := range tickets {
		ids = append(ids, id.Hex())
	}
	sort.Strings(ids)
	for _, idText := range ids {
		id := common.HexToHash(idText)
		saved := tickets[id]
		if saved.Owner == originalOwner {
			saved.Owner = owner
		} else if otherOwnerExpiry != 0 {
			saved.StartTime = otherOwnerExpiry - 30*24*3600
			saved.ExpireTime = otherOwnerExpiry
		}
		requireNoError(t, statedb.AddTicket(common.Ticket{Owner: saved.Owner, TicketBody: common.TicketBody{ID: id, Height: saved.Height, StartTime: saved.StartTime, ExpireTime: saved.ExpireTime}}))
	}
	header.MixDigest, err = statedb.UpdateTickets(header.Number, header.Time)
	requireNoError(t, err)
	header.Root, err = statedb.Commit(true)
	requireNoError(t, err)
	requireNoError(t, cache.TrieDB().Commit(header.Root, false, nil))
	parent := types.NewBlockWithHeader(&header)
	rawdb.WriteBlock(db, parent)
	rawdb.WriteTd(db, parent.Hash(), parent.NumberU64(), big.NewInt(1))
	rawdb.WriteCanonicalHash(db, parent.Hash(), parent.NumberU64())
	rawdb.WriteHeadBlockHash(db, parent.Hash())
	rawdb.WriteHeadHeaderHash(db, parent.Hash())
	rawdb.WriteHeadFastBlockHash(db, parent.Hash())
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	requireNoError(t, err)
	t.Cleanup(func() {
		chain.Stop()
		db.Close()
	})
	return &fixture{db: db, chain: chain, engine: engine, key: key, owner: owner, parent: parent}
}

func readRPCObservations(t *testing.T) map[int]json.RawMessage {
	t.Helper()
	data, err := os.ReadFile("../../docs/evidence/restart-2026-09-23/responses.json")
	requireNoError(t, err)
	var observations []rpcObservation
	requireNoError(t, json.Unmarshal(data, &observations))
	values := make(map[int]json.RawMessage)
	for _, observation := range observations {
		values[observation.ID] = observation.Result
	}
	return values
}

func requireNoError(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func decimal(t *testing.T, value string) *big.Int {
	t.Helper()
	result, ok := new(big.Int).SetString(value, 10)
	if !ok {
		t.Fatalf("invalid decimal %q", value)
	}
	return result
}
