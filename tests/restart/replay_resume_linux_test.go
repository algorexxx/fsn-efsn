package restart

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/trie"
)

type replayIdentity struct {
	Format         int
	ExecutableHash string
	SourceGenesis  common.Hash
	SourceHead     common.Hash
	SourceConfig   string
	ReplayConfig   string
}

func prepareReplayDirectory(t *testing.T, backup inspectionBackup, directory string, end uint64) bool {
	t.Helper()
	if !filepath.IsAbs(directory) {
		t.Fatal("replay directory must be an absolute path")
	}
	executable, err := os.Executable()
	requireNoError(t, err)
	file, err := os.Open(executable)
	requireNoError(t, err)
	digest := sha256.New()
	_, err = io.Copy(digest, file)
	requireNoError(t, err)
	requireNoError(t, file.Close())
	sourceConfig, err := json.Marshal(backup.config)
	requireNoError(t, err)
	replayConfig, err := json.Marshal(core.DefaultGenesisBlock().Config)
	requireNoError(t, err)
	identity := replayIdentity{Format: 1, ExecutableHash: hex.EncodeToString(digest.Sum(nil)), SourceGenesis: rawdb.ReadCanonicalHash(backup.db, 0), SourceHead: backup.head.Hash(), SourceConfig: string(sourceConfig), ReplayConfig: string(replayConfig)}
	manifest := filepath.Join(directory, "replay-identity.json")
	resume := os.Getenv("FUSION_RESTART_REPLAY_RESUME") == "1"
	if !resume {
		if _, err := os.Lstat(directory); !os.IsNotExist(err) {
			t.Fatal("replay requires a new directory unless explicit validated resume is requested")
		}
		requireReplaySpace(t, filepath.Dir(directory))
		requireNoError(t, os.Mkdir(directory, 0700))
		encoded, err := json.MarshalIndent(identity, "", "  ")
		requireNoError(t, err)
		requireNoError(t, os.WriteFile(manifest, append(encoded, '\n'), 0600))
		return false
	}
	info, err := os.Lstat(directory)
	requireNoError(t, err)
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		t.Fatal("resume target must be an existing real directory")
	}
	encoded, err := os.ReadFile(manifest)
	requireNoError(t, err)
	var saved replayIdentity
	requireNoError(t, json.Unmarshal(encoded, &saved))
	if !reflect.DeepEqual(saved, identity) {
		t.Fatal("resume identity differs: require the same retained executable, source history and configurations")
	}
	requireReplaySpace(t, directory)
	verifyReplayHead(t, backup, directory, end)
	return true
}

func verifyReplayHead(t *testing.T, backup inspectionBackup, directory string, end uint64) {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(directory, 128, 64, "restart-resume-check", true)
	requireNoError(t, err)
	defer func() { requireNoError(t, db.Close()) }()
	if rawdb.ReadCanonicalHash(db, 0) != rawdb.ReadCanonicalHash(backup.db, 0) || !reflect.DeepEqual(rawdb.ReadChainConfig(db, rawdb.ReadCanonicalHash(db, 0)), core.DefaultGenesisBlock().Config) {
		t.Fatal("resume database genesis or configuration differs")
	}
	hash := rawdb.ReadHeadBlockHash(db)
	number := rawdb.ReadHeaderNumber(db, hash)
	if number == nil || *number > end || rawdb.ReadHeadHeaderHash(db) != hash || rawdb.ReadHeadFastBlockHash(db) != hash || rawdb.ReadCanonicalHash(db, *number) != hash || rawdb.ReadCanonicalHash(backup.db, *number) != hash {
		t.Fatal("resume head is inconsistent with the preserved history or requested end")
	}
	block := rawdb.ReadBlock(db, hash, *number)
	if block == nil || block.Hash() != hash {
		t.Fatal("resume head block is unavailable")
	}
	receipts := rawdb.ReadReceipts(db, hash, *number, core.DefaultGenesisBlock().Config)
	if types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || len(receipts) != len(block.Transactions()) || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() || types.CreateBloom(receipts) != block.Bloom() {
		t.Fatal("resume head transaction or receipt commitments differ")
	}
	actualTD, expectedTD := rawdb.ReadTd(db, hash, *number), rawdb.ReadTd(backup.db, hash, *number)
	if actualTD == nil || expectedTD == nil || actualTD.Cmp(expectedTD) != 0 {
		t.Fatal("resume cumulative difficulty differs from the preserved history")
	}
	statedb, err := state.New(block.Root(), block.MixDigest(), state.NewDatabase(db))
	requireNoError(t, err)
	tickets, err := statedb.AllTickets()
	requireNoError(t, err)
	requireNoError(t, state.AddCachedTickets(block.MixDigest(), tickets))
	requireNoError(t, statedb.Error())
	t.Logf("read-only resume preflight matched height=%d hash=%s", *number, hash.Hex())
}
