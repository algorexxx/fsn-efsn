package restart

import (
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"math/big"
	"os"
	"os/exec"
	"sync/atomic"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/core/vm"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/light"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func TestRestartAnchorEnforcement(t *testing.T) {
	if mode := os.Getenv("FUSION_ANCHOR_ENFORCEMENT_CHILD"); mode != "" {
		runAnchorEnforcement(t, mode)
		return
	}
	for _, mode := range []string{
		"full_batch", "stored_fork", "known_block", "headers", "direct_header", "receipts", "ancient_receipts",
		"fast_commit", "fast_missing_state", "fast_missing_body", "miner_write", "pruned_write", "missing_ancestor", "compatible_fork", "rewind_resync", "rollback_resync",
		"below_anchor_head", "config_snapshot", "body_validation", "network_identity", "genesis_setup",
		"startup_full", "startup_header", "startup_fast", "startup_masked_ancestry", "startup_index", "startup_missing", "startup_height", "startup_missing_body",
		"fresh_full_batch", "fresh_headers_receipts", "light_mode", "reset_identity", "chain_identity", "empty_anchor",
		"large_batch",
	} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartAnchorEnforcement$", "-test.v", "-test.timeout=40s")
			command.Env = append(os.Environ(), "FUSION_ANCHOR_ENFORCEMENT_CHILD="+mode)
			output, err := command.CombinedOutput()
			t.Logf("isolated anchor enforcement %s:\n%s", mode, output)
			requireNoError(t, err)
		})
	}
}

func runAnchorEnforcement(t *testing.T, mode string) {
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlCrit, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	datong.InitCheckPoints("")
	checkpointHeight := datong.LastCheckPoint
	var receiver *fixture
	var headerReads *anchorHeaderReads
	if mode == "large_batch" {
		headerReads = &anchorHeaderReads{Database: rawdb.NewMemoryDatabase()}
		receiver = newFixtureInDatabase(t, 0, headerReads)
	} else {
		receiver = newFixture(t)
	}
	returning := newFixture(t)
	advancePurchaseFixture(t, receiver, returning)
	shared := receiver.chain.CurrentBlock()
	accepted := roundTripBlocks(t, buildAnchorBranch(t, receiver, 4, 120))
	acceptedReceipts := make([]types.Receipts, len(accepted))
	for i, block := range accepted {
		acceptedReceipts[i] = receiver.chain.GetReceiptsByHash(block.Hash())
	}
	later := roundTripBlocks(t, buildAnchorBranch(t, returning, 5, 121))
	anchor, oldHead := accepted[0], accepted[3]
	_, err := receiver.chain.InsertChain(later[:1])
	requireNoError(t, err)
	for _, block := range later[1:] {
		rawdb.WriteBlock(receiver.db, block)
		rawdb.WriteTd(receiver.db, block.Hash(), block.NumberU64(), returning.chain.GetTd(block.Hash(), block.NumberU64()))
	}
	config := *receiver.chain.Config()
	config.RestartAnchor = &params.RestartAnchor{
		GenesisHash: receiver.chain.Genesis().Hash(), ChainID: config.ChainID.Uint64(), Number: anchor.NumberU64(), Hash: anchor.Hash(),
	}
	if mode == "fresh_full_batch" || mode == "fresh_headers_receipts" {
		requireNoError(t, receiver.chain.SetHead(shared.NumberU64()))
	}
	receiver.chain.Stop()
	switch mode {
	case "fast_missing_state":
		requireNoError(t, receiver.db.Delete(accepted[2].Root().Bytes()))
	case "fast_missing_body":
		rawdb.DeleteBody(receiver.db, accepted[2].Hash(), accepted[2].NumberU64())
	case "startup_full":
		rawdb.WriteHeadBlockHash(receiver.db, later[3].Hash())
	case "startup_header":
		rawdb.WriteHeadHeaderHash(receiver.db, later[4].Hash())
	case "startup_fast":
		rawdb.WriteHeadFastBlockHash(receiver.db, later[3].Hash())
	case "startup_masked_ancestry":
		rawdb.WriteHeadBlockHash(receiver.db, later[4].Hash())
		rawdb.WriteHeadHeaderHash(receiver.db, later[4].Hash())
		for _, block := range later[1:] {
			rawdb.WriteCanonicalHash(receiver.db, block.Hash(), block.NumberU64())
		}
	case "startup_index":
		rawdb.WriteCanonicalHash(receiver.db, later[1].Hash(), later[1].NumberU64())
	case "startup_missing":
		rawdb.DeleteHeader(receiver.db, accepted[1].Hash(), accepted[1].NumberU64())
	case "startup_height":
		rawdb.WriteHeadHeaderHash(receiver.db, accepted[0].Hash())
	case "startup_missing_body":
		rawdb.DeleteBody(receiver.db, oldHead.Hash(), oldHead.NumberU64())
	case "network_identity":
		config.RestartAnchor.GenesisHash = common.HexToHash("0xdead")
	case "chain_identity":
		config.RestartAnchor.ChainID++
	case "empty_anchor":
		config.RestartAnchor.Hash = common.Hash{}
	case "genesis_setup":
		rawdb.WriteHeadBlockHash(receiver.db, later[4].Hash())
		before := databaseDigest(t, receiver.db)
		genesis := &core.Genesis{Config: &config, GasLimit: receiver.parent.GasLimit(), Difficulty: big.NewInt(1)}
		_, _, err := core.SetupGenesisBlock(receiver.db, genesis)
		requireErrorContains(t, err, "restart anchor:")
		requireDatabaseUnchanged(t, receiver.db, before)
		return
	}
	beforeStartup := databaseDigest(t, receiver.db)
	receiver.engine = datong.New(config.DaTong, receiver.db)
	chain, err := core.NewBlockChain(receiver.db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, receiver.engine, vm.Config{}, nil)
	switch mode {
	case "startup_full", "startup_header", "startup_fast", "startup_masked_ancestry", "startup_index", "startup_missing", "startup_height", "startup_missing_body", "network_identity", "chain_identity", "empty_anchor":
		requireErrorContains(t, err, "restart anchor:")
		if chain != nil {
			t.Fatal("incompatible startup returned a usable chain")
		}
		requireDatabaseUnchanged(t, receiver.db, beforeStartup)
		t.Log("startup rejected without changing any database key/value")
		return
	}
	requireNoError(t, err)
	receiver.chain = chain
	if mode == "fresh_full_batch" || mode == "fresh_headers_receipts" {
		requireErrorContains(t, receiver.chain.CheckRestartReady(), "synchronization required")
	} else {
		requireNoError(t, receiver.chain.CheckRestartReady())
	}
	if receiver.chain.RestartAnchorHeight() != anchor.NumberU64() || datong.LastCheckPoint != checkpointHeight {
		t.Fatal("anchor was not installed separately from legacy checkpoints")
	}
	before := databaseDigest(t, receiver.db)
	headEvents := make(chan core.ChainHeadEvent, 8)
	subscription := receiver.chain.SubscribeChainHeadEvent(headEvents)
	defer subscription.Unsubscribe()
	expectedError := "restart anchor:"
	switch mode {
	case "full_batch":
		_, err = receiver.chain.InsertChain(later)
	case "stored_fork":
		_, err = receiver.chain.InsertChain(later[1:])
	case "known_block":
		_, err = receiver.chain.InsertChain(later[:1])
	case "headers":
		_, err = receiver.chain.InsertHeaderChain(blockHeaders(later[1:]), 1)
	case "direct_header":
		hc, initErr := core.NewHeaderChain(receiver.db, &config, receiver.engine, func() bool { return false })
		requireNoError(t, initErr)
		_, err = hc.WriteHeader(later[1].Header())
	case "receipts", "ancient_receipts":
		receipts := make([]types.Receipts, len(later))
		for i, block := range later {
			receipts[i] = returning.chain.GetReceiptsByHash(block.Hash())
		}
		var ancientLimit uint64
		if mode == "ancient_receipts" {
			ancientLimit = later[4].NumberU64()
		}
		_, err = receiver.chain.InsertReceiptChain(later[1:], receipts[1:], ancientLimit)
	case "fast_commit":
		err = receiver.chain.FastSyncCommitHead(later[0].Hash())
	case "fast_missing_state":
		err = receiver.chain.FastSyncCommitHead(accepted[2].Hash())
		expectedError = "missing trie node"
	case "fast_missing_body":
		err = receiver.chain.FastSyncCommitHead(accepted[2].Hash())
		expectedError = "non existent block"
	case "miner_write":
		_, err = receiver.chain.WriteBlockWithState(later[1], nil, nil)
	case "pruned_write":
		err = receiver.chain.WriteBlockWithoutState(later[1], big.NewInt(999))
	case "missing_ancestor":
		header := accepted[3].Header()
		header.ParentHash = common.HexToHash("0xbad")
		err = receiver.chain.WriteBlockWithoutState(types.NewBlockWithHeader(header), big.NewInt(999))
		requireErrorContains(t, err, "missing or corrupt ancestor")
	case "below_anchor_head":
		header := shared.Header()
		header.Difficulty = big.NewInt(999999)
		_, err = receiver.chain.WriteBlockWithState(types.NewBlockWithHeader(header), nil, nil)
		requireErrorContains(t, err, "restart anchor:")
		hc, initErr := core.NewHeaderChain(receiver.db, &config, receiver.engine, func() bool { return false })
		requireNoError(t, initErr)
		_, headerErr := hc.WriteHeader(header)
		requireErrorContains(t, headerErr, "restart anchor:")
		requireErrorContains(t, receiver.chain.FastSyncCommitHead(shared.Hash()), "below anchor")
	case "light_mode":
		_, err = light.NewLightChain(&anchorLightBackend{db: receiver.db}, &config, receiver.engine)
		requireErrorContains(t, err, "light sync is not supported")
	case "reset_identity":
		header := receiver.chain.Genesis().Header()
		header.Time++
		err = receiver.chain.ResetWithGenesisBlock(types.NewBlockWithHeader(header))
	case "config_snapshot":
		config.RestartAnchor.Hash = later[0].Hash()
		_, err = receiver.chain.InsertChain(later[1:])
	case "body_validation":
		txs := types.Transactions{accepted[0].Transactions()[0], accepted[0].Transactions()[0]}
		header := accepted[0].Header()
		header.TxHash = types.DeriveSha(txs, trie.NewStackTrie(nil))
		block := types.NewBlockWithHeader(header).WithBody(txs, nil)
		requireErrorContains(t, receiver.chain.Validator().ValidateBody(block), "buying more than one ticket")
		requireDatabaseUnchanged(t, receiver.db, before)
		return
	case "compatible_fork":
		requireNoError(t, returning.chain.SetHead(shared.NumberU64()))
		returning.importBlock(t, accepted[0])
		compatible := roundTripBlocks(t, buildAnchorBranch(t, returning, 5, 121))
		if returning.chain.GetTd(compatible[4].Hash(), compatible[4].NumberU64()).Cmp(receiver.chain.GetTd(oldHead.Hash(), oldHead.NumberU64())) <= 0 {
			t.Fatal("compatible fork is not heavier")
		}
		_, err = receiver.chain.InsertChain(compatible)
		requireNoError(t, err)
		requireCanonicalTip(t, receiver, compatible[4])
		if rawdb.ReadCanonicalHash(receiver.db, anchor.NumberU64()) != anchor.Hash() {
			t.Fatal("compatible fork displaced the anchor")
		}
		requireNoError(t, receiver.chain.CheckRestartReady())
		t.Log("heavier compatible fork adopted above the fixed anchor")
		return
	case "rewind_resync", "rollback_resync":
		if mode == "rewind_resync" {
			requireNoError(t, receiver.chain.SetHead(shared.NumberU64()))
		} else {
			hashes := make([]common.Hash, len(accepted))
			for i, block := range accepted {
				hashes[i] = block.Hash()
			}
			receiver.chain.Rollback(hashes)
			requireErrorContains(t, receiver.chain.FastSyncCommitHead(oldHead.Hash()), "fast-sync head is not canonical")
		}
		requireErrorContains(t, receiver.chain.CheckRestartReady(), "synchronization required")
		_, err = receiver.chain.WriteBlockWithState(accepted[0], nil, nil)
		requireErrorContains(t, err, "synchronization required")
		_, err = receiver.chain.InsertChain(later)
		requireErrorContains(t, err, "restart anchor:")
		_, err = receiver.chain.InsertChain(accepted)
		requireNoError(t, err)
		requireCanonicalTip(t, receiver, oldHead)
		requireNoError(t, receiver.chain.CheckRestartReady())
		t.Log("explicit rewind disabled mining; ordinary sync through the anchor restored readiness")
		return
	case "fresh_full_batch", "fresh_headers_receipts":
		if mode == "fresh_full_batch" {
			_, err = receiver.chain.InsertChain(accepted)
			requireNoError(t, err)
		} else {
			_, err = receiver.chain.InsertHeaderChain(blockHeaders(accepted), 1)
			requireNoError(t, err)
			_, err = receiver.chain.InsertReceiptChain(accepted, acceptedReceipts, 0)
			requireNoError(t, err)
			requireErrorContains(t, receiver.chain.CheckRestartReady(), "synchronization required")
			requireNoError(t, receiver.chain.FastSyncCommitHead(oldHead.Hash()))
			if receiver.chain.CurrentFastBlock().Hash() != oldHead.Hash() {
				t.Fatal("compatible receipts did not advance fast head")
			}
		}
		requireCanonicalTip(t, receiver, oldHead)
		requireNoError(t, receiver.chain.CheckRestartReady())
		receiver.chain.Stop()
		receiver.engine = datong.New(config.DaTong, receiver.db)
		receiver.chain, err = core.NewBlockChain(receiver.db, &core.CacheConfig{TrieDirtyDisabled: true}, &config, receiver.engine, vm.Config{}, nil)
		requireNoError(t, err)
		requireCanonicalTip(t, receiver, oldHead)
		requireNoError(t, receiver.chain.CheckRestartReady())
		t.Log("compatible synchronization through anchor survives clean reopening")
		return
	case "large_batch":
		hc, initErr := core.NewHeaderChain(receiver.db, &config, receiver.engine, func() bool { return false })
		requireNoError(t, initErr)
		next := func(parent *types.Header) *types.Header {
			header := types.CopyHeader(parent)
			header.Number = new(big.Int).Add(parent.Number, common.Big1)
			header.ParentHash = parent.Hash()
			header.Difficulty = big.NewInt(1)
			header.Time++
			return header
		}
		for i := 0; i < 8192; i++ {
			_, err := hc.WriteHeader(next(hc.CurrentHeader()))
			requireNoError(t, err)
		}
		headers := make([]*types.Header, 600)
		parent := hc.CurrentHeader()
		for i := range headers {
			headers[i] = next(parent)
			parent = headers[i]
		}
		headerReads.reads.Store(0)
		_, err = hc.InsertHeaderChain(headers, func(header *types.Header) error {
			_, err := hc.WriteHeader(header)
			return err
		}, time.Now())
		requireNoError(t, err)
		reads := headerReads.reads.Load()
		t.Logf("unsigned headers isolate ancestry cost: 8192 stored descendants then 600 imports required %d header reads", reads)
		if reads > 1200 {
			t.Fatal("batch proof checks evicted stored-tip proof and rewalked old ancestry")
		}
		if hc.CurrentHeader().Hash() != headers[len(headers)-1].Hash() {
			t.Fatal("large eligible batch did not become canonical")
		}
		return
	default:
		t.Fatalf("unknown anchor enforcement mode %q", mode)
	}
	requireErrorContains(t, err, expectedError)
	requireDatabaseUnchanged(t, receiver.db, before)
	requireCanonicalTip(t, receiver, oldHead)
	if receiver.chain.CurrentHeader().Hash() != oldHead.Hash() || receiver.chain.CurrentFastBlock().Hash() != oldHead.Hash() {
		t.Fatal("rejected import changed an in-memory header or fast head")
	}
	select {
	case <-headEvents:
		t.Fatal("rejected import emitted a head event")
	default:
	}
	t.Log("incompatible input rejected without database, head or event changes")
}

type anchorLightBackend struct {
	light.OdrBackend
	db ethdb.Database
}

type anchorHeaderReads struct {
	ethdb.Database
	reads atomic.Uint64
}

func (db *anchorHeaderReads) Get(key []byte) ([]byte, error) {
	if len(key) == 41 && key[0] == 'h' {
		db.reads.Add(1)
	}
	return db.Database.Get(key)
}

func (b *anchorLightBackend) Database() ethdb.Database { return b.db }
func (b *anchorLightBackend) IndexerConfig() *light.IndexerConfig {
	return &light.IndexerConfig{}
}

func databaseDigest(t *testing.T, db ethdb.Database) common.Hash {
	t.Helper()
	hash := sha256.New()
	iterator := db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		for _, value := range [][]byte{iterator.Key(), iterator.Value()} {
			requireNoError(t, binary.Write(hash, binary.BigEndian, uint64(len(value))))
			_, err := hash.Write(value)
			requireNoError(t, err)
		}
	}
	requireNoError(t, iterator.Error())
	return common.BytesToHash(hash.Sum(nil))
}

func requireDatabaseUnchanged(t *testing.T, db ethdb.Database, before common.Hash) {
	t.Helper()
	if after := databaseDigest(t, db); after != before {
		t.Fatalf("rejection changed database: before=%s after=%s", before, after)
	}
}

func TestRestartAnchorConfiguration(t *testing.T) {
	if params.MainnetChainConfig.RestartAnchor != nil {
		t.Fatal("production anchor must remain unset pending reviewed recovery artifacts")
	}
	config := *params.MainnetChainConfig
	config.RestartAnchor = &params.RestartAnchor{GenesisHash: params.MainnetGenesisHash, ChainID: 32659, Number: 10, Hash: common.HexToHash("0x123")}
	anchor, err := config.RestartAnchorForGenesis(params.MainnetGenesisHash)
	requireNoError(t, err)
	if anchor != nil {
		t.Fatal("caller-supplied settings overrode the compiled mainnet rule")
	}
	encoded, err := json.Marshal(&config)
	requireNoError(t, err)
	var decoded params.ChainConfig
	requireNoError(t, json.Unmarshal(encoded, &decoded))
	if decoded.RestartAnchor != nil {
		t.Fatal("anchor was loaded from serialized configuration")
	}
}
