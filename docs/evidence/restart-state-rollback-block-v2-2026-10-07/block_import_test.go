package state_test

import (
	"crypto/ecdsa"
	"encoding/hex"
	"encoding/json"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
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
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type f11BlockCase struct {
	Name   string
	Prior  bool
	Zero   bool
	Revert bool
}

type f11BlockPrograms struct {
	Child  []byte
	Parent []byte
}

type f11BlockFixture struct {
	DB     ethdb.Database
	Chain  *core.BlockChain
	Engine *datong.DaTong
	Parent *types.Block
}

type f11BlockObservation struct {
	Child       state.F11AccountObservation
	Sender      string
	SenderNonce uint64
	Beneficiary string
	Miner       string
	Receipts    []f11ReceiptObservation
	Tickets     uint64
	Difficulty  string
	Order       uint64
}

type f11BlockManifest struct {
	Name          string
	Database      string
	Scheduled     bool
	ParentHash    common.Hash
	ParentTickets common.Hash
	Block         []byte
	Expected      f11BlockObservation
}

type f11BlockProcess struct {
	Phase      string
	PID        int
	Namespace  string
	CacheEmpty bool
	Head       common.Hash
	Root       common.Hash
	TicketRoot common.Hash
	Selected   common.Hash
	Actual     f11BlockObservation
}

type f11BlockEvidence struct {
	Manifest    f11BlockManifest
	ProducerPID int
	Commands    [][]string
	Logs        []string
	Results     []f11BlockProcess
}

func TestF11BlockImport(t *testing.T) {
	for _, mode := range []struct {
		Name      string
		Height    int64
		Scheduled bool
		Active    bool
	}{
		{"disabled", 15130081, false, false}, {"before", 15130080, true, false},
		{"at", 15130081, true, f11Candidate}, {"after", 15130082, true, f11Candidate},
	} {
		for _, tc := range []f11BlockCase{
			{"clean_revert_absent", false, false, true}, {"dirty_revert_absent", true, false, true},
			{"dirty_revert_zero", true, true, true}, {"dirty_success_absent", true, false, false},
		} {
			t.Run(mode.Name+"/"+tc.Name, func(t *testing.T) {
				root := t.TempDir()
				producer := f11SeedBlockChain(t, filepath.Join(root, "producer"), mode.Height, mode.Scheduled, tc)
				receiverPath := filepath.Join(root, "receiver")
				receiver := f11SeedBlockChain(t, receiverPath, mode.Height, mode.Scheduled, tc)
				if receiver.Parent.Hash() != producer.Parent.Hash() {
					t.Fatal("independent checkpoint construction differs")
				}
				receiver.Chain.Stop()
				f11Require(t, receiver.DB.Close())
				block := f11BuildBlock(t, producer, tc)
				encoded, err := rlp.EncodeToBytes(block)
				f11Require(t, err)
				manifest := f11BlockManifest{Name: t.Name(), Database: receiverPath, Scheduled: mode.Scheduled, ParentHash: producer.Parent.Hash(), ParentTickets: producer.Parent.MixDigest(), Block: encoded, Expected: f11ExpectedBlock(tc, mode.Active)}
				manifestPath := filepath.Join(root, "manifest.json")
				f11WriteJSON(t, manifestPath, manifest)
				evidence := f11BlockEvidence{Manifest: manifest, ProducerPID: os.Getpid()}
				outputDir := os.Getenv("F11_BLOCK_OUTPUT")
				if outputDir == "" {
					t.Fatal("missing evidence directory")
				}
				f11Require(t, os.MkdirAll(outputDir, 0700))
				for _, phase := range []string{"import", "cold"} {
					resultPath := filepath.Join(root, phase+".json")
					command := exec.Command(os.Args[0], "-test.run=^TestF11BlockReceiver$", "-test.v", "-test.timeout=45s")
					command.Env = append(os.Environ(), "F11_BLOCK_MANIFEST="+manifestPath, "F11_BLOCK_PHASE="+phase, "F11_BLOCK_RESULT="+resultPath)
					output, runErr := command.CombinedOutput()
					evidence.Commands = append(evidence.Commands, command.Args)
					evidence.Logs = append(evidence.Logs, string(output))
					f11WriteJSON(t, filepath.Join(outputDir, mode.Name+"_"+tc.Name+".json"), evidence)
					if runErr != nil {
						t.Fatalf("%s subprocess: %v\n%s", phase, runErr, output)
					}
					var result f11BlockProcess
					f11ReadJSON(t, resultPath, &result)
					evidence.Results = append(evidence.Results, result)
				}
				f11WriteJSON(t, filepath.Join(outputDir, mode.Name+"_"+tc.Name+".json"), evidence)
				for _, result := range evidence.Results {
					if result.PID == evidence.ProducerPID || !result.CacheEmpty || result.Head != block.Hash() || result.Root != block.Root() || result.TicketRoot != block.MixDigest() || !reflect.DeepEqual(result.Actual, manifest.Expected) {
						t.Fatalf("invalid subprocess result: %+v", result)
					}
				}
				t.Logf("F11BLOCK %s root=%s receipt=%s tickets=%s", t.Name(), block.Root(), block.ReceiptHash(), block.MixDigest())
			})
		}
	}
}

func f11SeedBlockChain(t *testing.T, path string, height int64, scheduled bool, tc f11BlockCase) f11BlockFixture {
	t.Helper()
	db := f11Open(t, path, false)
	config := f11ExecutionConfig(scheduled, true)
	genesis, err := (&core.Genesis{Config: config, GasLimit: 1000000, Difficulty: big.NewInt(1), Timestamp: 1700000000}).Commit(db)
	f11Require(t, err)
	cache := state.NewDatabase(db)
	seed, err := state.New(genesis.Root(), common.Hash{}, cache)
	f11Require(t, err)
	programs := f11BlockCode(tc.Revert)
	child, parent, beneficiary := common.Address{2}, common.Address{3}, common.Address{5}
	seed.SetCode(child, programs.Child)
	seed.SetCode(parent, programs.Parent)
	seed.SetNonce(child, 7)
	seed.SetState(child, common.Hash{8}, common.Hash{9})
	seed.SetBalance(crypto.PubkeyToAddress(f11SyntheticKey(t, 2).PublicKey), common.SystemAssetID, big.NewInt(1000000000000000))
	seed.SetBalance(child, common.SystemAssetID, big.NewInt(11))
	seed.SetBalance(beneficiary, common.SystemAssetID, big.NewInt(3))
	if tc.Zero {
		seed.SetBalance(child, common.Hash{2}, big.NewInt(0))
	}
	seed.SetTimeLockBalance(child, common.Hash{2}, f11PersistenceLock())
	seed.SetTimeLockBalance(child, common.SystemAssetID, new(common.TimeLock))
	owner := crypto.PubkeyToAddress(f11SyntheticKey(t, 1).PublicKey)
	for id := byte(1); id <= 4; id++ {
		f11Require(t, seed.AddTicket(common.Ticket{Owner: owner, TicketBody: common.TicketBody{ID: common.Hash{id}, Height: 0, StartTime: 1700000000, ExpireTime: 1702592000}}))
	}
	tickets, err := seed.UpdateTickets(big.NewInt(height-1), 1700000000)
	f11Require(t, err)
	seedRoot, err := seed.Commit(true)
	f11Require(t, err)
	f11Require(t, cache.TrieDB().Commit(seedRoot, false, nil))
	header := &types.Header{Number: big.NewInt(height - 1), ParentHash: genesis.Hash(), Root: seedRoot, Time: 1700000000, GasLimit: 1000000, Difficulty: big.NewInt(1), BaseFee: big.NewInt(1000000000), MixDigest: tickets, Extra: datong.GenerateGenesisExtraData(nil, 4), Coinbase: owner, UncleHash: types.EmptyUncleHash}
	parentBlock := types.NewBlockWithHeader(header)
	rawdb.WriteBlock(db, parentBlock)
	rawdb.WriteTd(db, parentBlock.Hash(), parentBlock.NumberU64(), big.NewInt(1))
	rawdb.WriteCanonicalHash(db, parentBlock.Hash(), parentBlock.NumberU64())
	rawdb.WriteHeadBlockHash(db, parentBlock.Hash())
	rawdb.WriteHeadHeaderHash(db, parentBlock.Hash())
	rawdb.WriteHeadFastBlockHash(db, parentBlock.Hash())
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	f11Require(t, err)
	t.Cleanup(chain.Stop)
	if chain.CurrentBlock().Hash() != parentBlock.Hash() {
		t.Fatal("checkpoint changed at startup")
	}
	return f11BlockFixture{DB: db, Chain: chain, Engine: engine, Parent: parentBlock}
}

func f11BuildBlock(t *testing.T, f f11BlockFixture, tc f11BlockCase) *types.Block {
	t.Helper()
	key := f11SyntheticKey(t, 1)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	header := &types.Header{Number: new(big.Int).Add(f.Parent.Number(), common.Big1), ParentHash: f.Parent.Hash(), Time: 1700000120, GasLimit: 1000000, BaseFee: big.NewInt(1000000000), Coinbase: owner}
	f11Require(t, f.Engine.Prepare(f.Chain, header))
	working, err := f.Chain.StateAt(f.Parent.Root(), f.Parent.MixDigest())
	f11Require(t, err)
	senderKey := f11SyntheticKey(t, 2)
	var txs types.Transactions
	if tc.Prior {
		tx, err := types.SignTx(types.NewTransaction(0, common.Address{2}, big.NewInt(1), 100000, big.NewInt(1000000000), []byte{1}), types.NewEIP155Signer(f.Chain.Config().ChainID), senderKey)
		f11Require(t, err)
		txs = append(txs, tx)
	}
	tx, err := types.SignTx(types.NewTransaction(uint64(len(txs)), common.Address{3}, big.NewInt(0), 100000, big.NewInt(1000000000), nil), types.NewEIP155Signer(f.Chain.Config().ChainID), senderKey)
	f11Require(t, err)
	txs = append(txs, tx)
	var receipts types.Receipts
	pool := new(core.GasPool).AddGas(header.GasLimit)
	for index, tx := range txs {
		working.Prepare(tx.Hash(), index)
		receipt, err := core.ApplyTransaction(f.Chain.Config(), f.Chain, &owner, pool, working, header, tx, &header.GasUsed, vm.Config{})
		f11Require(t, err)
		receipts = append(receipts, receipt)
	}
	block, err := f.Engine.Finalize(f.Chain, header, working, txs, nil, receipts)
	f11Require(t, err)
	signed := block.Header()
	payload, err := datong.SigningPayload(signed)
	f11Require(t, err)
	signature, err := crypto.Sign(crypto.Keccak256(payload), key)
	f11Require(t, err)
	copy(signed.Extra[len(signed.Extra)-65:], signature)
	return block.WithSeal(signed)
}

func TestF11BlockReceiver(t *testing.T) {
	path := os.Getenv("F11_BLOCK_MANIFEST")
	if path == "" {
		t.Skip("subprocess-only receiver")
	}
	var manifest f11BlockManifest
	f11ReadJSON(t, path, &manifest)
	var block types.Block
	f11Require(t, rlp.DecodeBytes(manifest.Block, &block))
	phase := os.Getenv("F11_BLOCK_PHASE")
	if phase != "import" && phase != "cold" {
		t.Fatal("unknown phase")
	}
	cacheEmpty := state.GetCachedTickets(manifest.ParentTickets) == nil && state.GetCachedTickets(block.MixDigest()) == nil
	if !cacheEmpty {
		t.Fatal("receiver did not start with empty ticket cache")
	}
	db := f11Open(t, manifest.Database, false)
	config := f11ExecutionConfig(manifest.Scheduled, true)
	engine := datong.New(config.DaTong, db)
	chain, err := core.NewBlockChain(db, &core.CacheConfig{TrieDirtyDisabled: true}, config, engine, vm.Config{}, nil)
	f11Require(t, err)
	t.Cleanup(chain.Stop)
	if phase == "import" {
		if chain.CurrentBlock().Hash() != manifest.ParentHash || chain.HasBlock(block.Hash(), block.NumberU64()) {
			t.Fatal("receiver was not at its unmodified checkpoint")
		}
		_, err = chain.InsertChain(types.Blocks{&block})
		f11Require(t, err)
	}
	for _, head := range []common.Hash{chain.CurrentBlock().Hash(), chain.CurrentHeader().Hash(), chain.CurrentFastBlock().Hash(), rawdb.ReadHeadBlockHash(db), rawdb.ReadHeadHeaderHash(db), rawdb.ReadHeadFastBlockHash(db), rawdb.ReadCanonicalHash(db, block.NumberU64())} {
		if head != block.Hash() {
			t.Fatal("canonical/head marker differs from imported block")
		}
	}
	if rawdb.ReadCanonicalHash(db, block.NumberU64()-1) != manifest.ParentHash {
		t.Fatal("checkpoint changed")
	}
	if chain.GetTd(block.Hash(), block.NumberU64()).Cmp(big.NewInt(6)) != 0 {
		t.Fatal("unexpected total difficulty")
	}
	current, err := chain.State()
	f11Require(t, err)
	actual := f11ObserveBlock(t, db, config, &block, current)
	ns, err := os.Readlink("/proc/self/ns/net")
	f11Require(t, err)
	snapshot, err := datong.NewSnapshotFromHeader(block.Header())
	f11Require(t, err)
	result := f11BlockProcess{Phase: phase, PID: os.Getpid(), Namespace: ns, CacheEmpty: cacheEmpty, Head: chain.CurrentBlock().Hash(), Root: block.Root(), TicketRoot: block.MixDigest(), Selected: snapshot.Selected, Actual: actual}
	f11WriteJSON(t, os.Getenv("F11_BLOCK_RESULT"), result)
	if !reflect.DeepEqual(actual, manifest.Expected) {
		got, _ := json.Marshal(actual)
		want, _ := json.Marshal(manifest.Expected)
		t.Fatalf("block result got=%s want=%s", got, want)
	}
	chain.Stop()
	f11Require(t, db.Close())
	t.Logf("F11RECEIVER %s %s pid=%d empty-ticket-cache=%v", manifest.Name, phase, os.Getpid(), cacheEmpty)
}

func f11ObserveBlock(t *testing.T, db ethdb.Database, config *params.ChainConfig, block *types.Block, current *state.StateDB) f11BlockObservation {
	t.Helper()
	sender := crypto.PubkeyToAddress(f11SyntheticKey(t, 2).PublicKey)
	actual := f11BlockObservation{Child: state.F11InspectAccount(current, common.Address{2}), Sender: current.GetBalance(common.SystemAssetID, sender).String(), SenderNonce: current.GetNonce(sender), Beneficiary: current.GetBalance(common.SystemAssetID, common.Address{5}).String(), Miner: current.GetBalance(common.SystemAssetID, block.Coinbase()).String(), Difficulty: block.Difficulty().String(), Order: block.Nonce()}
	receipts := rawdb.ReadReceipts(db, block.Hash(), block.NumberU64(), config)
	if len(receipts) != len(block.Transactions()) || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() || types.CreateBloom(receipts) != (types.Bloom{}) || block.Bloom() != (types.Bloom{}) {
		t.Fatal("stored receipt commitments differ")
	}
	for index, receipt := range receipts {
		tx := block.Transactions()[index]
		position := rawdb.ReadTxLookupEntry(db, tx.Hash())
		if position == nil || *position != block.NumberU64() || receipt.TxHash != tx.Hash() || receipt.BlockHash != block.Hash() || receipt.BlockNumber.Cmp(block.Number()) != 0 || receipt.TransactionIndex != uint(index) || len(receipt.Logs) != 0 || len(receipt.PostState) != 0 {
			t.Fatal("stored receipt identity or transaction lookup differs")
		}
		actual.Receipts = append(actual.Receipts, f11ReceiptObservation{Status: receipt.Status, Gas: receipt.GasUsed, Cumulative: receipt.CumulativeGasUsed, Index: receipt.TransactionIndex})
	}
	if block.GasUsed() != actual.Receipts[len(actual.Receipts)-1].Cumulative {
		t.Fatal("block gas differs from receipts")
	}
	snapshot, err := datong.NewSnapshotFromHeader(block.Header())
	f11Require(t, err)
	if snapshot.TicketNumber != 3 || len(snapshot.Retreat) != 0 {
		t.Fatal("unexpected ticket snapshot")
	}
	tickets, err := current.AllTickets()
	f11Require(t, err)
	actual.Tickets = tickets.NumberOfTickets()
	selectedFound := false
	for id := byte(1); id <= 4; id++ {
		if snapshot.Selected == (common.Hash{id}) {
			selectedFound = true
			if current.IsTicketExist(snapshot.Selected) {
				t.Fatal("selected ticket remains")
			}
			continue
		}
		ticket, err := current.GetTicket(common.Hash{id})
		f11Require(t, err)
		want := common.Ticket{Owner: block.Coinbase(), TicketBody: common.TicketBody{ID: common.Hash{id}, Height: 0, StartTime: 1700000000, ExpireTime: 1702592000}}
		if !reflect.DeepEqual(ticket, &want) {
			t.Fatal("unselected ticket changed")
		}
	}
	if !selectedFound {
		t.Fatal("selected ticket was not in fixture input")
	}
	if crypto.Keccak256Hash(current.GetData(common.TicketKeyAddress)) != block.MixDigest() {
		t.Fatal("stored ticket bytes differ from header commitment")
	}
	return actual
}

func f11ExpectedBlock(tc f11BlockCase, active bool) f11BlockObservation {
	programs := f11BlockCode(tc.Revert)
	child := state.F11AccountObservation{Exists: true, BalanceIDs: []common.Hash{common.SystemAssetID}, Balances: []string{"11"}, TimeLockIDs: []common.Hash{{2}, common.SystemAssetID}, TimeLocks: []*common.TimeLock{f11PersistenceLock(), {Items: []*common.TimeLockItem{}}}, Nonce: 7, Code: hex.EncodeToString(programs.Child), Storage: common.Hash{9}}
	want := f11BlockObservation{Child: child, Sender: "968742000000000", SenderNonce: 1, Beneficiary: "3", Miner: "312531258000000000", Receipts: []f11ReceiptObservation{{Status: 0, Gas: 31258, Cumulative: 31258, Index: 0}}, Tickets: 3, Difficulty: "5", Order: 0}
	if tc.Prior {
		want.Child.Balances = []string{"12"}
		want.Sender, want.SenderNonce, want.Miner = "947707999999999", 2, "312552292000000000"
		want.Receipts = []f11ReceiptObservation{{Status: 1, Gas: 21034, Cumulative: 21034, Index: 0}, {Status: 0, Gas: 31258, Cumulative: 52292, Index: 1}}
	}
	if tc.Zero || (tc.Prior && tc.Revert && !active) {
		want.Child.BalanceIDs = append(want.Child.BalanceIDs, common.Hash{2})
		want.Child.Balances = append(want.Child.Balances, "0")
	}
	if !tc.Revert {
		want.Child = state.F11AccountObservation{}
		want.Beneficiary = "15"
		want.Receipts[len(want.Receipts)-1].Status = 1
	}
	return want
}

func f11BlockCode(revert bool) f11BlockPrograms {
	child, beneficiary := common.Address{2}, common.Address{5}
	code := []byte{byte(vm.CALLDATASIZE), byte(vm.ISZERO), byte(vm.PUSH1), 6, byte(vm.JUMPI), byte(vm.STOP), byte(vm.JUMPDEST), byte(vm.PUSH20)}
	code = append(code, beneficiary[:]...)
	code = append(code, byte(vm.SELFDESTRUCT))
	parent := []byte{byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH1), 0, byte(vm.PUSH20)}
	parent = append(parent, child[:]...)
	parent = append(parent, byte(vm.PUSH3), 1, 0x86, 0xa0, byte(vm.CALL), byte(vm.PUSH1), 0, byte(vm.MSTORE), byte(vm.PUSH1), 32, byte(vm.PUSH1), 0)
	if revert {
		parent = append(parent, byte(vm.REVERT))
	} else {
		parent = append(parent, byte(vm.RETURN))
	}
	return f11BlockPrograms{Child: code, Parent: parent}
}

func f11SyntheticKey(t *testing.T, value byte) *ecdsa.PrivateKey {
	t.Helper()
	data := make([]byte, 32)
	data[31] = value
	key, err := crypto.ToECDSA(data)
	f11Require(t, err)
	return key
}

func f11WriteJSON(t *testing.T, path string, value interface{}) {
	t.Helper()
	data, err := json.MarshalIndent(value, "", "  ")
	f11Require(t, err)
	f11Require(t, os.WriteFile(path, append(data, '\n'), 0600))
}

func f11ReadJSON(t *testing.T, path string, value interface{}) {
	t.Helper()
	data, err := os.ReadFile(path)
	f11Require(t, err)
	f11Require(t, json.Unmarshal(data, value))
}
