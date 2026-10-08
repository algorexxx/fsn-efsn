package state_test

import (
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"math/big"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/eth"
	"github.com/FusionFoundation/efsn/v5/eth/tracers"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/miner"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

type f11APIMode struct {
	Name      string
	Height    int64
	Scheduled bool
	Active    bool
}

type f11APIBackend struct {
	*eth.EthAPIBackend
	States       []*state.StateDB
	EVMNumbers   []int64
	TraceNumbers []int64
}

func (b *f11APIBackend) GetEVM(ctx context.Context, msg core.Message, s *state.StateDB, header *types.Header, config *vm.Config) (*vm.EVM, func() error, error) {
	evm, cleanup, err := b.EthAPIBackend.GetEVM(ctx, msg, s, header, config)
	if err == nil {
		b.States = append(b.States, s)
		b.EVMNumbers = append(b.EVMNumbers, evm.Context.BlockNumber.Int64())
	}
	return evm, cleanup, err
}

func (b *f11APIBackend) StateAtBlock(ctx context.Context, block *types.Block, reexec uint64, base *state.StateDB, checkLive, preferDisk bool) (*state.StateDB, error) {
	s, err := b.EthAPIBackend.StateAtBlock(ctx, block, reexec, base, checkLive, preferDisk)
	if err == nil {
		b.States = append(b.States, s)
		b.TraceNumbers = append(b.TraceNumbers, block.Number().Int64())
	}
	return s, err
}

func (b *f11APIBackend) StateAtTransaction(ctx context.Context, block *types.Block, index int, reexec uint64) (core.Message, vm.BlockContext, *state.StateDB, error) {
	msg, vmctx, s, err := b.EthAPIBackend.StateAtTransaction(ctx, block, index, reexec)
	if err == nil {
		b.States = append(b.States, s)
		b.TraceNumbers = append(b.TraceNumbers, vmctx.BlockNumber.Int64())
	}
	return msg, vmctx, s, err
}

type f11APIObservation struct {
	Requested    int64
	Latest       int64
	EVMNumbers   []int64
	TraceNumbers []int64
	Child        state.F11AccountObservation
	Gas          uint64
	Failed       bool
	Return       string
	Roots        []common.Hash
}

func f11APIModes() []f11APIMode {
	return []f11APIMode{{"disabled", 15130081, false, false}, {"before", 15130080, true, false}, {"at", 15130081, true, f11Candidate}, {"after", 15130082, true, f11Candidate}}
}

func TestF11CallRuleSelection(t *testing.T) {
	for _, mode := range f11APIModes() {
		for _, selector := range []string{"number", "hash", "latest", "pending", "pending_fallback"} {
			for _, operation := range []string{"do_call", "public_call", "estimate", "trace_call"} {
				if selector == "pending_fallback" && operation != "do_call" {
					continue
				}
				t.Run(mode.Name+"/"+selector+"/"+operation, func(t *testing.T) {
					headHeight := mode.Height
					if selector == "number" || selector == "hash" {
						headHeight = 15130101
					}
					if selector == "pending" {
						headHeight = mode.Height - 1
					}
					fixture := f11SeedBlockChain(t, filepath.Join(t.TempDir(), "chain"), headHeight+1, mode.Scheduled, f11BlockCase{Revert: true})
					header := fixture.Parent.Header()
					if selector == "number" || selector == "hash" {
						previous := types.CopyHeader(header)
						previous.Number = big.NewInt(mode.Height - 1)
						previous.Time -= 15
						f11StoreAPIBlock(fixture.DB, types.NewBlockWithHeader(previous))
						header.Number = big.NewInt(mode.Height)
						header.ParentHash = previous.Hash()
						f11StoreAPIBlock(fixture.DB, types.NewBlockWithHeader(header))
					}
					var snapshot *state.StateDB
					var pending *types.Block
					if selector == "pending" {
						header.Number = big.NewInt(mode.Height)
						header.ParentHash = fixture.Parent.Hash()
						header.Time += 15
						pending = types.NewBlockWithHeader(header)
						var err error
						snapshot, err = fixture.Chain.State()
						f11Require(t, err)
					}
					backend := &f11APIBackend{EthAPIBackend: eth.F11FixtureBackend(fixture.Chain, fixture.DB, miner.F11FixturePending(fixture.Chain, pending, snapshot))}
					query := rpc.BlockNumberOrHashWithNumber(rpc.BlockNumber(mode.Height))
					switch selector {
					case "hash":
						query = rpc.BlockNumberOrHashWithHash(header.Hash(), true)
					case "latest":
						query = rpc.BlockNumberOrHashWithNumber(rpc.LatestBlockNumber)
					case "pending", "pending_fallback":
						query = rpc.BlockNumberOrHashWithNumber(rpc.PendingBlockNumber)
					}
					from := crypto.PubkeyToAddress(f11SyntheticKey(t, 2).PublicKey)
					to, gas := common.Address{3}, hexutil.Uint64(100000)
					args := ethapi.TransactionArgs{From: &from, To: &to, Gas: &gas}
					before := f11APIDBDigest(t, fixture.DB)
					actual := f11APIObservation{Requested: mode.Height, Latest: headHeight}
					ctx := context.Background()
					switch operation {
					case "do_call":
						result, err := ethapi.DoCall(ctx, backend, args, query, nil, 2*time.Second, 1000000)
						f11Require(t, err)
						actual.Gas, actual.Failed, actual.Return = result.UsedGas, result.Failed(), hex.EncodeToString(result.Revert())
					case "public_call":
						_, err := ethapi.NewPublicBlockChainAPI(backend).Call(ctx, args, query, nil)
						f11AssertRevert(t, err)
						actual.Failed, actual.Return = true, "0000000000000000000000000000000000000000000000000000000000000001"
					case "estimate":
						value, err := ethapi.DoEstimateGas(ctx, backend, args, query, 1000000)
						f11AssertRevert(t, err)
						if value != 0 {
							t.Fatal("reverted call received an estimate")
						}
						actual.Failed, actual.Return = true, "0000000000000000000000000000000000000000000000000000000000000001"
					case "trace_call":
						result, err := tracers.NewAPI(backend).TraceCall(ctx, args, query, nil)
						f11Require(t, err)
						f11ObserveTrace(t, &actual, result)
					}
					if len(backend.States) == 0 {
						t.Fatal("execution state was not observed")
					}
					actual.Child = state.F11InspectAccount(backend.States[len(backend.States)-1], common.Address{2})
					actual.EVMNumbers, actual.TraceNumbers = backend.EVMNumbers, backend.TraceNumbers
					want := f11ExpectedAPIChild("11", mode.Active)
					if !reflect.DeepEqual(actual.Child, want) {
						t.Fatalf("raw child differs: got=%+v want=%+v", actual.Child, want)
					}
					for _, number := range append(append([]int64{}, backend.EVMNumbers...), backend.TraceNumbers...) {
						if number != mode.Height {
							t.Fatal("wrong execution/requested block number")
						}
					}
					wantGas := uint64(31258)
					if operation == "public_call" || operation == "estimate" {
						wantGas = 0
					}
					if actual.Gas != wantGas || !actual.Failed || actual.Return != "0000000000000000000000000000000000000000000000000000000000000001" {
						t.Fatalf("unexpected call result: %+v", actual)
					}
					if snapshot != nil && !reflect.DeepEqual(state.F11InspectAccount(snapshot, common.Address{2}), f11ExpectedAPIChild("11", true)) {
						t.Fatal("pending snapshot mutated")
					}
					if before != f11APIDBDigest(t, fixture.DB) {
						t.Fatal("call changed stored database keys/values")
					}
					f11LogAPI(t, actual)
				})
			}
		}
	}
}

func TestF11HistoricalRuleSelection(t *testing.T) {
	for _, mode := range f11APIModes() {
		for _, operation := range []string{"transaction", "block_number", "block_hash", "intermediate_roots"} {
			t.Run(mode.Name+"/"+operation, func(t *testing.T) {
				fixture := f11SeedBlockChain(t, filepath.Join(t.TempDir(), "chain"), mode.Height, mode.Scheduled, f11BlockCase{Prior: true, Revert: true})
				block := f11BuildBlock(t, fixture, f11BlockCase{Prior: true, Revert: true})
				_, err := fixture.Chain.InsertChain(types.Blocks{block})
				f11Require(t, err)
				fixture.Chain.Stop()
				later := block.Header()
				later.Number = big.NewInt(15130101)
				later.ParentHash = block.Hash()
				later.Time += 120
				latest := types.NewBlockWithHeader(later)
				f11StoreAPIBlock(fixture.DB, latest)
				rawdb.WriteHeadBlockHash(fixture.DB, latest.Hash())
				rawdb.WriteHeadHeaderHash(fixture.DB, latest.Hash())
				rawdb.WriteHeadFastBlockHash(fixture.DB, latest.Hash())
				chain, err := core.NewBlockChain(fixture.DB, &core.CacheConfig{TrieDirtyDisabled: true}, fixture.Chain.Config(), datong.New(fixture.Chain.Config().DaTong, fixture.DB), vm.Config{}, nil)
				f11Require(t, err)
				t.Cleanup(chain.Stop)
				backend := &f11APIBackend{EthAPIBackend: eth.F11FixtureBackend(chain, fixture.DB, nil)}
				api := tracers.NewAPI(backend)
				actual := f11APIObservation{Requested: mode.Height, Latest: 15130101}
				before := f11APIDBDigest(t, fixture.DB)
				ctx := context.Background()
				switch operation {
				case "transaction":
					result, err := api.TraceTransaction(ctx, block.Transactions()[1].Hash(), nil)
					f11Require(t, err)
					f11ObserveTrace(t, &actual, result)
				case "block_number", "block_hash":
					if operation == "block_number" {
						results, err := api.TraceBlockByNumber(ctx, rpc.BlockNumber(mode.Height), nil)
						f11Require(t, err)
						if len(results) != 2 || results[0].Error != "" || results[1].Error != "" {
							t.Fatal("incomplete block trace")
						}
						f11AssertPriorTrace(t, results[0].Result)
						f11ObserveTrace(t, &actual, results[1].Result)
					} else {
						results, err := api.TraceBlockByHash(ctx, block.Hash(), nil)
						f11Require(t, err)
						if len(results) != 2 || results[0].Error != "" || results[1].Error != "" {
							t.Fatal("incomplete block trace")
						}
						f11AssertPriorTrace(t, results[0].Result)
						f11ObserveTrace(t, &actual, results[1].Result)
					}
				case "intermediate_roots":
					actual.Roots, err = api.IntermediateRoots(ctx, block.Hash(), nil)
					f11Require(t, err)
					if len(actual.Roots) != 2 || actual.Roots[0] == (common.Hash{}) || actual.Roots[1] == (common.Hash{}) {
						t.Fatal("incomplete intermediate roots")
					}
				}
				if len(backend.States) != 1 {
					t.Fatal("unexpected trace state requests")
				}
				actual.Child = state.F11InspectAccount(backend.States[0], common.Address{2})
				actual.TraceNumbers = backend.TraceNumbers
				if !reflect.DeepEqual(actual.Child, f11ExpectedAPIChild("12", mode.Active)) {
					t.Fatalf("wrong replay rule/state: %+v", actual)
				}
				requestedStateHeight := mode.Height - 1
				if operation == "transaction" {
					requestedStateHeight = mode.Height
				}
				if !reflect.DeepEqual(actual.TraceNumbers, []int64{requestedStateHeight}) {
					t.Fatal("trace selected wrong context/base state")
				}
				if operation != "intermediate_roots" && (actual.Gas != 31258 || !actual.Failed || actual.Return != "0000000000000000000000000000000000000000000000000000000000000001") {
					t.Fatal("wrong trace result")
				}
				if before != f11APIDBDigest(t, fixture.DB) {
					t.Fatal("trace changed stored database keys/values")
				}
				f11LogAPI(t, actual)
			})
		}
	}
}

func f11ExpectedAPIChild(balance string, active bool) state.F11AccountObservation {
	want := f11ExpectedBlock(f11BlockCase{Revert: true}, true).Child
	want.Balances = []string{balance}
	if !active {
		want.BalanceIDs = append(want.BalanceIDs, common.Hash{2})
		want.Balances = append(want.Balances, "<nil>")
	}
	return want
}

func f11AssertRevert(t *testing.T, err error) {
	t.Helper()
	code, ok := err.(rpc.Error)
	if !ok || code.ErrorCode() != 3 {
		t.Fatalf("expected revert code 3, got %v", err)
	}
	data, ok := err.(rpc.DataError)
	if !ok || data.ErrorData() != "0x0000000000000000000000000000000000000000000000000000000000000001" {
		t.Fatal("wrong revert bytes")
	}
}

func f11ObserveTrace(t *testing.T, actual *f11APIObservation, result interface{}) {
	t.Helper()
	trace, ok := result.(*ethapi.ExecutionResult)
	if !ok || len(trace.StructLogs) == 0 {
		t.Fatal("missing structured trace")
	}
	actual.Gas, actual.Failed, actual.Return = trace.Gas, trace.Failed, trace.ReturnValue
}

func f11AssertPriorTrace(t *testing.T, result interface{}) {
	t.Helper()
	trace, ok := result.(*ethapi.ExecutionResult)
	if !ok || trace.Gas != 21034 || trace.Failed || trace.ReturnValue != "" {
		t.Fatal("wrong preceding transaction trace")
	}
}

func f11StoreAPIBlock(db ethdb.Database, block *types.Block) {
	rawdb.WriteBlock(db, block)
	rawdb.WriteCanonicalHash(db, block.Hash(), block.NumberU64())
	rawdb.WriteTd(db, block.Hash(), block.NumberU64(), big.NewInt(1))
}

func f11APIDBDigest(t *testing.T, db ethdb.Database) string {
	t.Helper()
	h := sha256.New()
	it := db.NewIterator(nil, nil)
	defer it.Release()
	var size [8]byte
	for it.Next() {
		binary.BigEndian.PutUint64(size[:], uint64(len(it.Key())))
		h.Write(size[:])
		h.Write(it.Key())
		binary.BigEndian.PutUint64(size[:], uint64(len(it.Value())))
		h.Write(size[:])
		h.Write(it.Value())
	}
	f11Require(t, it.Error())
	return hex.EncodeToString(h.Sum(nil))
}

func f11LogAPI(t *testing.T, actual f11APIObservation) {
	t.Helper()
	encoded, err := json.Marshal(actual)
	f11Require(t, err)
	t.Logf("F11API %s %s", t.Name(), encoded)
}
