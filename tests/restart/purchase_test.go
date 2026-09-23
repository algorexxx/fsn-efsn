package restart

import (
	"context"
	"math/big"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/misc"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type purchaseBackend struct {
	ethapi.Backend
	chain *core.BlockChain
}

func (b *purchaseBackend) StateAndHeaderByNumber(_ context.Context, number rpc.BlockNumber) (*state.StateDB, *types.Header, error) {
	if number != rpc.LatestBlockNumber {
		panic("purchase fixture only supports latest state")
	}
	statedb, err := b.chain.State()
	return statedb, b.chain.CurrentBlock().Header(), err
}

func TestLongPurchaseRequiresHistoricalRefundDespitePoolAdmission(t *testing.T) {
	for _, refund := range []bool{false, true} {
		name := "before_refund"
		if refund {
			name = "after_refund"
		}
		t.Run(name, func(t *testing.T) {
			f := newFixture(t)
			if refund {
				f.importBlock(t, f.buildBlock(t, f.parent.Time()+120, false))
			}
			api := ethapi.NewPublicFusionAPI(&purchaseBackend{chain: f.chain})
			end := hexutil.Uint64(common.TimeLockForever)
			args := common.BuyTicketArgs{FusionBaseArgs: common.FusionBaseArgs{From: f.owner}, End: &end}
			tx := f.signPurchase(t, f.chain.CurrentBlock().Time(), uint64(end))
			pool := f.newPool(t)
			expected := "not enough time lock or asset balance"

			built, apiErr := api.BuildBuyTicketSendTxArgs(context.Background(), args)
			poolErr := pool.AddRemote(tx)

			requireNoError(t, poolErr)
			if !refund {
				requireErrorContains(t, apiErr, expected)
				requireErrorContains(t, f.applyPurchase(t, tx), expected)
				return
			}
			requireNoError(t, apiErr)
			rpcTx := f.signPurchaseData(t, *built.Input)
			if rpcTx.Hash() != tx.Hash() {
				t.Fatal("RPC constructed a different purchase")
			}
			f.importBlock(t, f.buildBlockWithTransactions(t, f.chain.CurrentBlock().Time()+120, []*types.Transaction{rpcTx}))
			statedb, err := f.chain.State()
			requireNoError(t, err)
			parentHash := f.chain.CurrentBlock().ParentHash()
			if !statedb.IsTicketExist(crypto.Keccak256Hash(f.owner[:], parentHash[:])) {
				t.Fatal("accepted purchase did not create its ticket")
			}
		})
	}
}

func TestDefaultHistoricalPurchaseFailsPoolAdmission(t *testing.T) {
	f := newFixture(t)
	f.importBlock(t, f.buildBlock(t, f.parent.Time()+120, false))
	api := ethapi.NewPublicFusionAPI(&purchaseBackend{chain: f.chain})
	args := common.BuyTicketArgs{FusionBaseArgs: common.FusionBaseArgs{From: f.owner}}
	built, err := api.BuildBuyTicketSendTxArgs(context.Background(), args)
	requireNoError(t, err)
	var envelope common.FSNCallParam
	var purchase common.BuyTicketParam
	requireNoError(t, rlp.DecodeBytes(*built.Input, &envelope))
	requireNoError(t, rlp.DecodeBytes(envelope.Data, &purchase))
	pool := f.newPool(t)
	tx := f.signPurchaseData(t, *built.Input)

	err = pool.AddLocal(tx)

	requireErrorContains(t, err, "TimeLockItem time is invalid")
	if purchase.Start != 1759826750 || purchase.End != 1762418750 {
		t.Fatalf("unexpected default historical interval: %+v", purchase)
	}
}

func TestPresentDayPurchaseStartRejectedOnHistoricalHead(t *testing.T) {
	f := newFixture(t)
	f.importBlock(t, f.buildBlock(t, f.parent.Time()+120, false))
	api := ethapi.NewPublicFusionAPI(&purchaseBackend{chain: f.chain})
	start, end := hexutil.Uint64(jumpTime), hexutil.Uint64(common.TimeLockForever)
	args := common.BuyTicketArgs{FusionBaseArgs: common.FusionBaseArgs{From: f.owner}, Start: &start, End: &end}
	pool := f.newPool(t)
	tx := f.signPurchase(t, uint64(start), uint64(end))
	expected := "BuyTicket start must be lower than latest block time + 3 hour"

	_, apiErr := api.BuildBuyTicketSendTxArgs(context.Background(), args)
	poolErr := pool.AddRemote(tx)

	requireErrorContains(t, apiErr, expected)
	requireErrorContains(t, poolErr, expected)
}

func (f *fixture) newPool(t *testing.T) *core.TxPool {
	t.Helper()
	config := core.DefaultTxPoolConfig
	config.Journal = ""
	pool := core.NewTxPool(config, f.chain.Config(), f.chain)
	t.Cleanup(pool.Stop)
	return pool
}

func (f *fixture) applyPurchase(t *testing.T, tx *types.Transaction) error {
	t.Helper()
	parent := f.chain.CurrentBlock()
	header := &types.Header{ParentHash: parent.Hash(), Number: new(big.Int).Add(parent.Number(), big.NewInt(1)), Time: parent.Time() + 120, GasLimit: parent.GasLimit(), Coinbase: f.owner, Difficulty: new(big.Int), BaseFee: misc.CalcBaseFee(f.chain.Config(), parent.Header())}
	requireNoError(t, f.engine.Prepare(f.chain, header))
	statedb, err := f.chain.State()
	requireNoError(t, err)
	statedb.Prepare(tx.Hash(), 0)
	_, err = core.ApplyTransaction(f.chain.Config(), f.chain, &f.owner, new(core.GasPool).AddGas(header.GasLimit), statedb, header, tx, &header.GasUsed, vm.Config{})
	return err
}

func requireErrorContains(t *testing.T, err error, expected string) {
	t.Helper()
	if err == nil || !strings.Contains(err.Error(), expected) {
		t.Fatalf("expected %q, got %v", expected, err)
	}
}
