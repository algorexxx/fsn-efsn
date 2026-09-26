package restart

import (
	"math/big"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type controlledReservePrefix struct {
	pair      *denseMinerPair
	funder    *fixture
	affected  int
	blocks    types.Blocks
	originals types.Transactions
}

func buildControlledReservePrefix(t *testing.T) *controlledReservePrefix {
	t.Helper()
	keyBytes := make([]byte, 32)
	keyBytes[31] = 3
	key, err := crypto.ToECDSA(keyBytes)
	requireNoError(t, err)
	funder := &fixture{key: key, owner: crypto.PubkeyToAddress(key.PublicKey)}
	allocation := core.GenesisAlloc{funder.owner: {Balance: decimal(t, "11000000000000000000000")}}
	pair := seedDenseMinerPairWithWindow(t, "12020102000000000000000", 2, allocation, uint64(time.Now().Unix())-24*3600, 30*24*3600)
	result := &controlledReservePrefix{pair: pair, funder: funder, affected: -1}
	state, err := pair.miners[0].chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	for _, ticket := range tickets.ToTicketSlice() {
		if ticket.Height == 0 || ticket.ExpireTime != ticket.StartTime+30*24*3600 {
			t.Fatal("controlled prefix requires only funded 30-day tickets")
		}
	}
	for i, miner := range pair.miners {
		if tickets.NumberOfTicketsByAddress(miner.owner) == 2 {
			result.affected = i
		}
	}
	if result.affected == -1 {
		t.Fatal("controlled prefix lacks an owner with exactly two tickets")
	}
	owner := pair.miners[result.affected].owner
	lost := 0
	for step := 0; step < 32 && lost < 2; step++ {
		block := appendControlledReserveBlock(t, pair, 1-result.affected, 1-result.affected, nil)
		snapshot, err := datong.NewSnapshotFromHeader(block.Header())
		requireNoError(t, err)
		if len(snapshot.Retreat) > 0 {
			if len(snapshot.Retreat) != 1 {
				t.Fatal("two-owner prefix unexpectedly retreated multiple owners")
			}
			lost++
			t.Logf("controlled prefix first-retreat=%d affected=%s block=%d hash=%s ticket=%s", lost, owner.Hex(), block.NumberU64(), block.Hash().Hex(), snapshot.Retreat[0].Hex())
		}
	}
	state, err = pair.miners[0].chain.State()
	requireNoError(t, err)
	tickets, err = state.AllTickets()
	requireNoError(t, err)
	head := pair.miners[0].chain.CurrentBlock()
	need := common.NewTimeLock(&common.TimeLockItem{StartTime: head.Time(), EndTime: head.Time() + 30*24*3600, Value: decimal(t, "5000000000000000000000")})
	if lost != 2 || tickets.NumberOfTicketsByAddress(owner) != 0 || state.GetTimeLockBalance(common.SystemAssetID, owner).Cmp(need) >= 0 || state.GetBalance(common.SystemAssetID, owner).Cmp(decimal(t, "5000000000000000000000")) >= 0 {
		t.Fatal("prefix did not reach exactly two losses, zero tickets and inadequate current purchase funds")
	}
	for number := uint64(1); number <= head.NumberU64(); number++ {
		result.blocks = append(result.blocks, pair.miners[0].chain.GetBlockByNumber(number))
	}
	result.originals = signControlledMissingPurchases(t, pair.miners[result.affected], 7)
	t.Logf("controlled zero-ticket parent height=%d hash=%s state=%s tickets=%s affected=%s nonce=%d liquid-wei=%s locks=%s; identical prefix and seven signed purchases used in every branch", head.NumberU64(), head.Hash().Hex(), head.Root().Hex(), head.MixDigest().Hex(), owner.Hex(), state.GetNonce(owner), state.GetBalance(common.SystemAssetID, owner), state.GetTimeLockBalance(common.SystemAssetID, owner))
	closeDenseMinerPair(t, pair)
	return result
}

func appendControlledReserveBlock(t *testing.T, pair *denseMinerPair, producer, replenisher int, extra types.Transactions) *types.Block {
	t.Helper()
	state, err := pair.miners[0].chain.State()
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	parent := pair.miners[0].chain.CurrentBlock()
	txs := append(types.Transactions(nil), extra...)
	buyer := pair.miners[replenisher]
	if tickets.NumberOfTicketsByAddress(buyer.owner) < 2 {
		txs = append(txs, buyer.signPurchase(t, parent.Time(), parent.Time()+30*24*3600))
	}
	block := pair.miners[producer].buildBlockWithTransactions(t, parent.Time()+120, txs)
	for _, miner := range pair.miners {
		miner.importBlock(t, block)
	}
	return block
}

func signControlledMissingPurchases(t *testing.T, owner *fixture, count int) types.Transactions {
	t.Helper()
	state, err := owner.chain.State()
	requireNoError(t, err)
	start := owner.chain.CurrentBlock().Time()
	body, err := rlp.EncodeToBytes(&common.BuyTicketParam{Start: start, End: start + 30*24*3600})
	requireNoError(t, err)
	data, err := rlp.EncodeToBytes(&common.FSNCallParam{Func: common.BuyTicketFunc, Data: body})
	requireNoError(t, err)
	var result types.Transactions
	for i := 0; i < count; i++ {
		tx, err := types.SignTx(types.NewTransaction(state.GetNonce(owner.owner)+uint64(i), common.FSNCallAddress, new(big.Int), 100000, big.NewInt(2000000000), data), types.LatestSigner(owner.chain.Config()), owner.key)
		requireNoError(t, err)
		result = append(result, tx)
	}
	return result
}

func replayControlledReservePrefix(t *testing.T, prefix *controlledReservePrefix) *denseMinerPair {
	t.Helper()
	pair := &denseMinerPair{genesis: prefix.pair.genesis}
	for i, miner := range prefix.pair.miners {
		pair.miners[i] = &fixture{key: miner.key, owner: miner.owner}
	}
	openDenseMinerDatabases(t, pair)
	for _, block := range prefix.blocks {
		for _, miner := range pair.miners {
			miner.importBlock(t, block)
		}
	}
	for _, miner := range pair.miners {
		if miner.chain.CurrentBlock().Hash() != prefix.blocks[len(prefix.blocks)-1].Hash() {
			t.Fatal("controlled branch starts from a different prefix")
		}
	}
	return pair
}
