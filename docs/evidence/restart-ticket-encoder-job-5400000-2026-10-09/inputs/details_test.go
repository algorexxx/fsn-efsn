package restart

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
	"golang.org/x/sys/unix"
)

type replayObservation struct {
	Number           uint64
	Hash             common.Hash
	Root             common.Hash
	TicketCommitment common.Hash
	TransactionRoot  common.Hash
	ReceiptRoot      common.Hash
	Bloom            types.Bloom
	TotalDifficulty  string
	Transactions     int
	Receipts         int
	HeaderRLP        string
	TicketCount      *uint64 `json:",omitempty"`
}

func TestCandidateReplayReference(t *testing.T) {
	requireReadOnlyMount(t, os.Getenv("FUSION_RESTART_CHAINDATA"))
	backup := openInspectionBackup(t)
	writeReplayObservation(t, observeReplayBlock(t, backup.db, false))
}

func TestCandidateReplayColdDetails(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_INSPECT_REPLAY_DIR")
	requireReadOnlyMount(t, directory)
	db, err := rawdb.NewLevelDBDatabase(directory, 128, 64, "candidate-cold-details", true)
	requireNoError(t, err)
	defer func() { requireNoError(t, db.Close()) }()
	writeReplayObservation(t, observeReplayBlock(t, db, true))
}

func requireReadOnlyMount(t *testing.T, directory string) {
	t.Helper()
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(directory, &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("observation requires a read-only mount")
	}
}

func observeReplayBlock(t *testing.T, db ethdb.Database, withTickets bool) replayObservation {
	t.Helper()
	const height = uint64(5400000)
	hash := rawdb.ReadCanonicalHash(db, height)
	block := rawdb.ReadBlock(db, hash, height)
	if block == nil || block.Hash() != hash || block.NumberU64() != height {
		t.Fatal("missing or inconsistent endpoint block")
	}
	config := rawdb.ReadChainConfig(db, rawdb.ReadCanonicalHash(db, 0))
	if config == nil {
		t.Fatal("missing chain configuration")
	}
	receipts := rawdb.ReadReceipts(db, hash, height, config)
	if types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || len(receipts) != len(block.Transactions()) || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() || types.CreateBloom(receipts) != block.Bloom() {
		t.Fatal("endpoint transaction or receipt commitments differ")
	}
	td := rawdb.ReadTd(db, hash, height)
	if td == nil {
		t.Fatal("missing total difficulty")
	}
	header, err := rlp.EncodeToBytes(block.Header())
	requireNoError(t, err)
	observation := replayObservation{Number: height, Hash: hash, Root: block.Root(), TicketCommitment: block.MixDigest(), TransactionRoot: block.TxHash(), ReceiptRoot: block.ReceiptHash(), Bloom: block.Bloom(), TotalDifficulty: td.String(), Transactions: len(block.Transactions()), Receipts: len(receipts), HeaderRLP: hex.EncodeToString(header)}
	if withTickets {
		if state.GetCachedTickets(block.MixDigest()) != nil {
			t.Fatal("cold observation began with cached endpoint tickets")
		}
		statedb, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db))
		requireNoError(t, err)
		tickets, err := statedb.AllTickets()
		requireNoError(t, err)
		requireNoError(t, state.AddCachedTickets(block.MixDigest(), tickets))
		requireNoError(t, statedb.Error())
		count := uint64(tickets.NumberOfTickets())
		observation.TicketCount = &count
	}
	return observation
}

func writeReplayObservation(t *testing.T, observation replayObservation) {
	t.Helper()
	encoded, err := json.Marshal(observation)
	requireNoError(t, err)
	t.Logf("candidate endpoint observation: %s", encoded)
}
