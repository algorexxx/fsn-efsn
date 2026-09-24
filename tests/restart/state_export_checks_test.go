package restart

import (
	"bytes"
	"context"
	"errors"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func stateExportFixture(t *testing.T, db ethdb.Database) common.Hash {
	t.Helper()
	cache := state.NewDatabase(db)
	statedb, err := state.New(common.Hash{}, common.Hash{}, cache)
	requireNoError(t, err)
	owner := common.HexToAddress("0x1234")
	statedb.SetBalance(owner, common.SystemAssetID, big.NewInt(7))
	statedb.SetCode(owner, []byte{0x60, 0x01, 0x00})
	statedb.SetState(owner, common.HexToHash("0x01"), common.HexToHash("0x02"))
	statedb.SetData(common.HexToAddress("0x5678"), []byte{0x11, 0x22, 0x33, 0x44})
	root, err := statedb.Commit(false)
	requireNoError(t, err)
	requireNoError(t, cache.TrieDB().Commit(root, false, nil))
	return root
}

func TestStateExportIntegrity(t *testing.T) {
	for _, damage := range []string{"none", "missing_root", "corrupt_root", "missing_storage", "corrupt_storage", "missing_code", "corrupt_code", "missing_native_data", "corrupt_native_data", "legacy_code", "stopped", "stopped_before_commit", "occupied_target"} {
		t.Run(damage, func(t *testing.T) {
			source, target := rawdb.NewMemoryDatabase(), rawdb.NewMemoryDatabase()
			defer source.Close()
			defer target.Close()
			root := stateExportFixture(t, source)
			codeHash := crypto.Keccak256Hash([]byte{0x60, 0x01, 0x00})
			accounts, err := state.NewDatabase(source).OpenTrie(root)
			requireNoError(t, err)
			encoded, err := accounts.TryGet(common.HexToAddress("0x1234").Bytes())
			requireNoError(t, err)
			var account state.Account
			requireNoError(t, rlp.DecodeBytes(encoded, &account))
			switch damage {
			case "missing_root":
				rawdb.DeleteTrieNode(source, root)
			case "corrupt_root":
				rawdb.WriteTrieNode(source, root, []byte{0xff})
			case "missing_storage":
				rawdb.DeleteTrieNode(source, account.Root)
			case "corrupt_storage":
				rawdb.WriteTrieNode(source, account.Root, []byte{0xff})
			case "missing_code":
				rawdb.DeleteCode(source, codeHash)
			case "corrupt_code":
				rawdb.WriteCode(source, codeHash, []byte{0xff})
			case "missing_native_data":
				rawdb.DeleteCode(source, crypto.Keccak256Hash([]byte{0x11, 0x22, 0x33, 0x44}))
			case "corrupt_native_data":
				rawdb.WriteCode(source, crypto.Keccak256Hash([]byte{0x11, 0x22, 0x33, 0x44}), []byte{0xff})
			case "legacy_code":
				rawdb.DeleteCode(source, codeHash)
				requireNoError(t, source.Put(codeHash.Bytes(), []byte{0x60, 0x01, 0x00}))
			case "occupied_target":
				requireNoError(t, target.Put([]byte("unrelated"), []byte("retain")))
			}
			before := databaseDigest(t, source)
			_, err = exportState(source, target, root, func(current stateExportProgress) error {
				if damage == "stopped" || damage == "stopped_before_commit" && current.FetchedNodes > 0 {
					return errors.New("injected stop")
				}
				return nil
			})
			requireDatabaseUnchanged(t, source, before)
			if damage != "none" && damage != "legacy_code" {
				if err == nil {
					t.Fatal("export accepted incomplete source, stop or occupied target")
				}
				if damage == "occupied_target" {
					value, err := target.Get([]byte("unrelated"))
					requireNoError(t, err)
					if !bytes.Equal(value, []byte("retain")) {
						t.Fatal("rejected target was altered")
					}
				}
				return
			}
			requireNoError(t, err)
			result, err := inspectState(target, root, func(stateInspection) {})
			requireNoError(t, err)
			if result != (stateInspection{Accounts: 2, StorageLeaves: 1, CodeReferences: 2, CodeBytes: 7}) {
				t.Fatalf("export changed fixture inventory: %+v", result)
			}
			_, err = exportState(source, target, root, func(stateExportProgress) error { return nil })
			requireErrorContains(t, err, "empty target")
		})
	}
}

func TestStateExportDirectory(t *testing.T) {
	path := filepath.Join(t.TempDir(), "export")
	identity := stateExportIdentity{Format: 1}
	requireNoError(t, createStateExportDirectory(path, identity))
	before, err := os.ReadFile(filepath.Join(path, "identity.json"))
	requireNoError(t, err)
	requireErrorContains(t, createStateExportDirectory(path, stateExportIdentity{Format: 2}), "new directory")
	after, err := os.ReadFile(filepath.Join(path, "identity.json"))
	requireNoError(t, err)
	if !bytes.Equal(before, after) {
		t.Fatal("rejected export reuse changed its identity")
	}
	if _, err := os.Stat(filepath.Join(path, "verified.json")); !os.IsNotExist(err) {
		t.Fatal("new export was marked verified")
	}
	requireErrorContains(t, createStateExportDirectory("relative-export", identity), "absolute")
}

func TestStateExportCrash(t *testing.T) {
	if phase := os.Getenv("FUSION_STATE_EXPORT_CRASH"); phase != "" {
		source := rawdb.NewMemoryDatabase()
		defer source.Close()
		root := stateExportFixture(t, source)
		path := os.Getenv("FUSION_STATE_EXPORT_CRASH_PATH")
		requireNoError(t, createStateExportDirectory(path, stateExportIdentity{Format: 1}))
		requireNoError(t, os.WriteFile(filepath.Join(path, "root.txt"), []byte(root.Hex()), 0600))
		plain, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", false)
		requireNoError(t, err)
		cut, err := strconv.Atoi(os.Getenv("FUSION_STATE_EXPORT_CRASH_CUT"))
		requireNoError(t, err)
		db := &crashDatabase{Database: plain, armed: true, cut: cut, phase: phase}
		_, err = exportState(source, db, root, func(stateExportProgress) error { return nil })
		requireNoError(t, err)
		t.Fatal("requested export crash boundary was not reached")
	}
	for _, phase := range []string{"before", "after"} {
		t.Run(phase, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "export")
			ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestStateExportCrash$", "-test.v", "-test.timeout=20s")
			command.Env = append(os.Environ(), "FUSION_STATE_EXPORT_CRASH="+phase, "FUSION_STATE_EXPORT_CRASH_PATH="+path, "FUSION_STATE_EXPORT_CRASH_CUT=1")
			output, err := command.CombinedOutput()
			var exit *exec.ExitError
			if !errors.As(err, &exit) || exit.ExitCode() != 86 || !strings.Contains(string(output), "CRASH "+phase) || strings.Contains(string(output), "WARNING: DATA RACE") {
				t.Fatalf("unexpected export child exit: %v\n%s", err, output)
			}
			db, err := rawdb.NewLevelDBDatabase(filepath.Join(path, "chaindata"), 16, 16, "", true)
			requireNoError(t, err)
			defer db.Close()
			encoded, err := os.ReadFile(filepath.Join(path, "root.txt"))
			requireNoError(t, err)
			_, err = inspectState(db, common.HexToHash(string(encoded)), func(stateInspection) {})
			if (err == nil) != (phase == "after") {
				t.Fatalf("unexpected interrupted fixture completeness: %v", err)
			}
			if _, err := os.Stat(filepath.Join(path, "verified.json")); !os.IsNotExist(err) {
				t.Fatal("interrupted extraction was marked verified")
			}
			requireErrorContains(t, createStateExportDirectory(path, stateExportIdentity{Format: 1}), "new directory")
		})
	}
}
