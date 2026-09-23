package restart

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func TestPreservedBackupReadOnly(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_CHAINDATA")
	if directory == "" {
		t.Skip("set FUSION_RESTART_CHAINDATA to a verified disposable copy for offline inspection")
	}
	if _, err := os.Stat(filepath.Join(directory, "ancient")); !os.IsNotExist(err) {
		t.Fatal("this probe expects the observed LevelDB-only backup; review freezer handling for a different layout")
	}
	values := readRPCObservations(t)
	var expectedHead, expectedGenesis types.Header
	var expectedTickets map[common.Hash]common.TicketDisplay
	var expectedLocks common.TimeLock
	var expectedLiquid string
	var expectedChainID, expectedNonce hexutil.Uint64
	requireNoError(t, json.Unmarshal(values[1], &expectedChainID))
	requireNoError(t, json.Unmarshal(values[2], &expectedGenesis))
	requireNoError(t, json.Unmarshal(values[3], &expectedHead))
	requireNoError(t, json.Unmarshal(values[7], &expectedTickets))
	requireNoError(t, json.Unmarshal(values[9], &expectedLiquid))
	requireNoError(t, json.Unmarshal(values[10], &expectedLocks))
	requireNoError(t, json.Unmarshal(values[12], &expectedNonce))
	db, err := rawdb.NewLevelDBDatabase(directory, 256, 64, "restart-readonly", true)
	requireNoError(t, err)
	t.Cleanup(func() { requireNoError(t, db.Close()) })
	genesis := rawdb.ReadCanonicalHash(db, 0)
	if genesis != expectedGenesis.Hash() {
		t.Fatalf("unexpected genesis: %s", genesis.Hex())
	}
	config := rawdb.ReadChainConfig(db, genesis)
	if config == nil || config.ChainID == nil || config.ChainID.Uint64() != uint64(expectedChainID) {
		t.Fatal("missing or unexpected stored chain configuration")
	}
	for name, hash := range map[string]common.Hash{
		"header": rawdb.ReadHeadHeaderHash(db),
		"block":  rawdb.ReadHeadBlockHash(db),
		"fast":   rawdb.ReadHeadFastBlockHash(db),
	} {
		if hash != expectedHead.Hash() {
			t.Fatalf("unexpected %s head: %s", name, hash.Hex())
		}
	}
	height := expectedHead.Number.Uint64()
	for _, number := range []uint64{0, 1, 1000000, height - 1024, height - 128, height - 127, height - 1, height} {
		hash := rawdb.ReadCanonicalHash(db, number)
		block := rawdb.ReadBlock(db, hash, number)
		if block == nil || block.Hash() != hash {
			t.Fatalf("missing or inconsistent canonical block at %d", number)
		}
		if number > 0 && block.ParentHash() != rawdb.ReadCanonicalHash(db, number-1) {
			t.Fatalf("parent link mismatch at %d", number)
		}
		receipts := rawdb.ReadReceipts(db, hash, number, config)
		if len(receipts) != len(block.Transactions()) || types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() {
			t.Fatalf("transaction or receipt commitment mismatch at %d", number)
		}
		_, stateErr := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db))
		t.Logf("sample height=%d hash=%s transactions=%d receipts=%d stateOpenError=%v", number, hash.Hex(), len(block.Transactions()), len(receipts), stateErr)
	}
	statedb, err := state.New(expectedHead.Root, expectedHead.MixDigest, state.NewDatabase(db))
	requireNoError(t, err)
	tickets, err := statedb.AllTickets()
	requireNoError(t, err)
	if !reflect.DeepEqual(tickets.ToMap(), expectedTickets) {
		t.Fatal("head tickets differ from the saved gateway observations")
	}
	requireNoError(t, state.AddCachedTickets(expectedHead.MixDigest, tickets))
	owner := common.HexToAddress("0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1")
	if statedb.GetBalance(common.SystemAssetID, owner).String() != expectedLiquid || !reflect.DeepEqual(statedb.GetTimeLockBalance(common.SystemAssetID, owner), &expectedLocks) || statedb.GetNonce(owner) != uint64(expectedNonce) {
		t.Fatal("operator account differs from the saved balance, time-lock, or nonce observation")
	}
	requireNoError(t, statedb.Error())
	t.Logf("matched genesis=%s chainID=%s all three heads=%s height=%d root=%s ticketCommitment=%s tickets=%d owners=%d ownerBalance=%s ownerNonce=%d", genesis.Hex(), config.ChainID, expectedHead.Hash().Hex(), height, expectedHead.Root.Hex(), expectedHead.MixDigest.Hex(), tickets.NumberOfTickets(), len(tickets), expectedLiquid, expectedNonce)
}
