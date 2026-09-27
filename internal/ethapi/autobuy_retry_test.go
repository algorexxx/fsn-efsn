package ethapi

import (
	"bytes"
	"context"
	"math/big"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type ticketRetryBackend struct {
	Backend
	db         ethdb.Database
	state      *state.StateDB
	header     *types.Header
	current    *types.Header
	owner      common.Address
	mining     bool
	pending    types.Transactions
	queued     types.Transactions
	retries    types.Transactions
	now        time.Time
	retryTimes []time.Time
}

func (b *ticketRetryBackend) Coinbase() (common.Address, error) { return b.owner, nil }
func (b *ticketRetryBackend) ChainConfig() *params.ChainConfig  { return params.MainnetChainConfig }
func (b *ticketRetryBackend) ChainDb() ethdb.Database           { return b.db }
func (b *ticketRetryBackend) IsMining() bool                    { return b.mining }
func (b *ticketRetryBackend) CurrentHeader() *types.Header      { return b.current }
func (b *ticketRetryBackend) StateAndHeaderByNumber(context.Context, rpc.BlockNumber) (*state.StateDB, *types.Header, error) {
	return b.state, b.header, nil
}
func (b *ticketRetryBackend) TxPoolContent() (map[common.Address]types.Transactions, map[common.Address]types.Transactions) {
	return map[common.Address]types.Transactions{b.owner: b.pending}, map[common.Address]types.Transactions{b.owner: b.queued}
}
func (b *ticketRetryBackend) RebroadcastTx(_ context.Context, tx *types.Transaction) error {
	b.retries = append(b.retries, tx)
	b.retryTimes = append(b.retryTimes, b.now)
	return nil
}
func (b *ticketRetryBackend) GetTransaction(context.Context, common.Hash) (*types.Transaction, common.Hash, uint64, uint64, error) {
	return nil, common.Hash{}, 0, 0, nil
}
func (b *ticketRetryBackend) GetPoolTransactionByPredicate(predicate func(*types.Transaction) bool) *types.Transaction {
	for _, tx := range b.pending {
		if predicate(tx) {
			return tx
		}
	}
	return nil
}

func TestPendingAutomaticTicketRetry(t *testing.T) {
	for _, mode := range []string{"pending", "not-due", "queued", "nonce-gap", "replaced", "another-ticket", "cancelled", "disabled", "not-mining", "changed-head", "consumed", "head-storm"} {
		t.Run(mode, func(t *testing.T) {
			db := rawdb.NewMemoryDatabase()
			defer db.Close()
			statedb, err := state.New(common.Hash{}, common.Hash{}, state.NewDatabase(db))
			if err != nil {
				t.Fatal(err)
			}
			key, err := crypto.HexToECDSA("0000000000000000000000000000000000000000000000000000000000000002")
			if err != nil {
				t.Fatal(err)
			}
			owner := crypto.PubkeyToAddress(key.PublicKey)
			purchase, err := rlp.EncodeToBytes(&common.BuyTicketParam{Start: 1790488672, End: 1793083767})
			if err != nil {
				t.Fatal(err)
			}
			payload, err := rlp.EncodeToBytes(&common.FSNCallParam{Func: common.BuyTicketFunc, Data: purchase})
			if err != nil {
				t.Fatal(err)
			}
			tx, err := types.SignTx(types.NewTransaction(9, common.FSNCallAddress, new(big.Int), 21224, big.NewInt(1000000001), payload), types.LatestSigner(params.MainnetChainConfig), key)
			if err != nil {
				t.Fatal(err)
			}
			saved, err := tx.MarshalBinary()
			if err != nil {
				t.Fatal(err)
			}
			if err := db.Put(automaticTicketKey(owner), saved); err != nil {
				t.Fatal(err)
			}
			header := &types.Header{Number: big.NewInt(15130124), Time: 1790490000}
			b := &ticketRetryBackend{db: db, state: statedb, owner: owner, header: header, current: header, mining: true, pending: types.Transactions{tx}}
			statedb.SetNonce(owner, 9)
			api := &FusionTransactionAPI{b: b, pubapi: NewPublicFusionAPI(b), nonceLock: new(AddrLocker)}
			common.SetAutoBuyTicketEnabled(true)
			defer common.SetAutoBuyTicketEnabled(false)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			due, wantError := true, ""
			switch mode {
			case "not-due":
				due = false
			case "queued":
				b.pending, b.queued = nil, types.Transactions{tx}
			case "nonce-gap":
				statedb.SetNonce(owner, 8)
				wantError = "needs nonce 9, current nonce is 8"
			case "replaced":
				b.pending = types.Transactions{types.NewTransaction(9, owner, new(big.Int), 21000, big.NewInt(2), nil)}
				wantError = "was replaced"
			case "another-ticket":
				b.queued = types.Transactions{types.NewTransaction(10, common.FSNCallAddress, new(big.Int), 21224, big.NewInt(2), payload)}
				wantError = "another ticket purchase"
			case "cancelled":
				cancel()
				wantError = "context canceled"
			case "disabled":
				common.SetAutoBuyTicketEnabled(false)
			case "not-mining":
				b.mining = false
			case "changed-head":
				b.current = &types.Header{Number: big.NewInt(15130125)}
				wantError = "head changed"
			case "consumed":
				statedb.SetNonce(owner, 10)
				wantError = "not enough time lock or asset balance"
			}

			err = api.reconcileTicketPurchase(ctx, due)
			if mode == "head-storm" {
				b.retries, b.retryTimes = nil, nil
				previous := fusionTransactionAPI
				fusionTransactionAPI = api
				defer func() { fusionTransactionAPI = previous }()
				start := time.Unix(1790490000, 0)
				steps := []time.Duration{0, time.Second, 2 * time.Second, 4999 * time.Millisecond, 5 * time.Second, 5001 * time.Millisecond, 9999 * time.Millisecond, 10 * time.Second}
				ticks := make(chan time.Time, len(steps))
				for range steps {
					ticks <- start
				}
				index := 0
				runAutoBuyTicket(ctx, true, func() time.Time {
					if index == len(steps) {
						cancel()
						return b.now
					}
					b.now = start.Add(steps[index])
					b.header = &types.Header{Number: big.NewInt(int64(15130124 + index)), Time: 1790490000}
					b.current = b.header
					index++
					return b.now
				}, ticks)
				if !reflect.DeepEqual(b.retryTimes, []time.Time{start, start.Add(5 * time.Second), start.Add(10 * time.Second)}) {
					t.Fatalf("head-storm retry times: %v", b.retryTimes)
				}
				for _, retry := range b.retries {
					if retry.Hash() != tx.Hash() {
						t.Fatal("head storm changed purchase")
					}
				}
				b.retries = nil
			}

			if (err != nil) != (wantError != "") || err != nil && !strings.Contains(err.Error(), wantError) {
				t.Fatalf("error=%v, want %q", err, wantError)
			}
			if mode == "pending" {
				if len(b.retries) != 1 {
					t.Fatalf("retries=%d", len(b.retries))
				}
				actual, err := b.retries[0].MarshalBinary()
				if err != nil || !bytes.Equal(actual, saved) {
					t.Fatal("retry changed signed bytes")
				}
			} else if len(b.retries) != 0 {
				t.Fatal("guarded purchase was rebroadcast")
			}
			actual, _ := db.Get(automaticTicketKey(owner))
			if mode == "consumed" {
				if len(actual) != 0 {
					t.Fatal("consumed intent not retired")
				}
			} else if !bytes.Equal(actual, saved) {
				t.Fatal("retry changed persisted intent")
			}
		})
	}
}
