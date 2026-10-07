package recovery

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math/big"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/params"
)

type f11ObservedDatabase struct {
	ethdb.Database
	writes int
}

func (db *f11ObservedDatabase) Put(key, value []byte) error {
	db.writes++
	return db.Database.Put(key, value)
}

func (db *f11ObservedDatabase) Delete(key []byte) error {
	db.writes++
	return db.Database.Delete(key)
}

func (db *f11ObservedDatabase) NewBatch() ethdb.Batch {
	return ethdb.HookedBatch{Batch: db.Database.NewBatch(), OnPut: func([]byte, []byte) { db.writes++ }, OnDelete: func([]byte) { db.writes++ }}
}

func TestF11StartupConfiguration(t *testing.T) {
	cases := []struct {
		name          string
		custom        bool
		head          uint64
		stored        *big.Int
		supplied      bool
		next          *big.Int
		missingConfig bool
		missingHeader bool
		wrongID       bool
		unscheduled   bool
		want          *big.Int
		wantError     string
	}{
		{name: "legacy_before", head: 99, want: big.NewInt(100)},
		{name: "legacy_at", head: 100, wantError: "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{name: "legacy_after", head: 101, wantError: "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{name: "matching_at", head: 100, stored: big.NewInt(100), want: big.NewInt(100)},
		{name: "matching_after", head: 101, stored: big.NewInt(100), want: big.NewInt(100)},
		{name: "conflicting_before", head: 99, stored: big.NewInt(101), wantError: "suicide time-lock fix: mainnet activation differs from this build"},
		{name: "conflicting_after", head: 101, stored: big.NewInt(101), wantError: "suicide time-lock fix: mainnet activation differs from this build"},
		{name: "supplied_conflict", head: 99, supplied: true, next: big.NewInt(101), wantError: "suicide time-lock fix: mainnet activation differs from this build"},
		{name: "wrong_identity", head: 99, wrongID: true, wantError: "suicide time-lock fix: mainnet chain identity mismatch"},
		{name: "missing_config_before", head: 99, missingConfig: true, want: big.NewInt(100)},
		{name: "missing_config_at", head: 100, missingConfig: true, wantError: "suicide time-lock fix: missing configuration after activation"},
		{name: "missing_header", head: 99, missingHeader: true, wantError: "missing block number for head header hash"},
		{name: "inactive_missing_header", head: 99, missingHeader: true, unscheduled: true, wantError: "missing block number for head header hash"},
		{name: "unselected_normal", head: 101, unscheduled: true},
		{name: "custom_same_id_no_schedule", custom: true, head: 101},
		{name: "custom_schedule", custom: true, head: 101, stored: big.NewInt(3), want: big.NewInt(3)},
		{name: "custom_future_add", custom: true, head: 99, supplied: true, next: big.NewInt(100), want: big.NewInt(100)},
		{name: "custom_zero_rewind", custom: true, head: 1, supplied: true, next: big.NewInt(1), wantError: "suicide time-lock fix: incompatible execution schedule:"},
		{name: "custom_remove_active", custom: true, head: 101, stored: big.NewInt(100), supplied: true, wantError: "suicide time-lock fix: incompatible execution schedule:"},
		{name: "custom_move_active", custom: true, head: 101, stored: big.NewInt(100), supplied: true, next: big.NewInt(101), wantError: "suicide time-lock fix: incompatible execution schedule:"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f11MainnetSchedule(t, !tc.unscheduled)
			db := &f11ObservedDatabase{Database: rawdb.NewMemoryDatabase()}
			t.Cleanup(func() { db.Close() })
			genesis := f11Genesis(tc.custom, tc.stored)
			if tc.wrongID {
				genesis.Config.ChainID = big.NewInt(1)
			}
			f11SeedHead(t, db, genesis, tc.head)
			genesisHash := rawdb.ReadCanonicalHash(db, 0)
			if tc.missingConfig {
				f11Require(t, db.Delete(append([]byte("ethereum-config-"), genesisHash.Bytes()...)))
			}
			if tc.missingHeader {
				rawdb.DeleteHeaderNumber(db, rawdb.ReadHeadHeaderHash(db))
			}
			var supplied *core.Genesis
			if tc.supplied {
				supplied = f11Genesis(tc.custom, tc.next)
			}
			before := f11Entries(t, db)
			db.writes = 0

			actual, hash, err := core.SetupGenesisBlock(db, supplied)
			after := f11Entries(t, db)

			if tc.wantError != "" {
				if err == nil || !strings.HasPrefix(err.Error(), tc.wantError) {
					t.Fatalf("error = %v; want prefix %q", err, tc.wantError)
				}
				if _, rewind := err.(*params.ConfigCompatError); rewind {
					t.Fatal("error enters the backend automatic-rewind branch")
				}
				if db.writes != 0 || !reflect.DeepEqual(after, before) {
					t.Fatalf("rejection changed database or attempted writes: %d", db.writes)
				}
				return
			}
			if err != nil || actual == nil || hash != genesisHash {
				t.Fatalf("startup result = %v, %s, %v", actual, hash, err)
			}
			if !reflect.DeepEqual(actual.SuicideTimeLockFixBlock, tc.want) {
				t.Fatalf("schedule = %v, want %v", actual.SuicideTimeLockFixBlock, tc.want)
			}
			if tc.custom && !tc.supplied && (db.writes != 0 || !reflect.DeepEqual(after, before)) {
				t.Fatal("custom stored configuration changed without supplied genesis")
			}
		})
	}
}

func TestF11ReaderConfiguration(t *testing.T) {
	cases := []struct {
		name      string
		custom    bool
		head      uint64
		stored    *big.Int
		want      *big.Int
		wantError string
	}{
		{"legacy_before", false, 99, nil, big.NewInt(100), ""},
		{"legacy_at", false, 100, nil, nil, "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{"legacy_after", false, 101, nil, nil, "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{"matching_after", false, 101, big.NewInt(100), big.NewInt(100), ""},
		{"conflict", false, 101, big.NewInt(101), nil, "suicide time-lock fix: mainnet activation differs from this build"},
		{"custom_same_id", true, 101, nil, nil, ""},
		{"custom_schedule", true, 101, big.NewInt(3), big.NewInt(3), ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f11MainnetSchedule(t, true)
			db := &f11ObservedDatabase{Database: rawdb.NewMemoryDatabase()}
			t.Cleanup(func() { db.Close() })
			f11SeedHead(t, db, f11Genesis(tc.custom, tc.stored), tc.head)
			before := f11Entries(t, db)
			db.writes = 0

			reader, err := NewReader(db)
			after := f11Entries(t, db)

			if db.writes != 0 || !reflect.DeepEqual(after, before) {
				t.Fatalf("reader attempted writes: %d", db.writes)
			}
			if tc.wantError != "" {
				if err == nil || err.Error() != tc.wantError || reader != nil {
					t.Fatalf("reader = %v, %v; want nil, %s", reader, err, tc.wantError)
				}
				return
			}
			if err != nil || reader == nil || !reflect.DeepEqual(reader.Config().SuicideTimeLockFixBlock, tc.want) {
				t.Fatalf("reader/config result = %v, %v", reader, err)
			}
		})
	}
}

func TestF11ConfigurationColdReopen(t *testing.T) {
	f11MainnetSchedule(t, true)
	path := filepath.Join(t.TempDir(), "chain")
	db := f11Open(t, path, false)
	f11SeedHead(t, db, f11Genesis(false, nil), 99)
	before := f11Entries(t, db)
	f11Require(t, db.Close())
	db = f11Open(t, path, true)
	reader, err := NewReader(db)
	f11Require(t, err)
	effective := *params.MainnetChainConfig
	if !reflect.DeepEqual(reader.Config(), &effective) || !reflect.DeepEqual(f11Entries(t, db), before) {
		t.Fatal("read-only reopen changed stored data or resolved the wrong configuration")
	}
	f11Require(t, db.Close())
	db = f11Open(t, path, false)
	resolved, _, err := core.SetupGenesisBlock(db, nil)
	f11Require(t, err)
	if !reflect.DeepEqual(resolved, &effective) {
		t.Fatal("startup and offline reader disagree")
	}
	persisted := f11Entries(t, db)
	f11Require(t, db.Close())
	db = f11Open(t, path, false)
	defer db.Close()
	loaded, _, err := core.SetupGenesisBlock(db, nil)
	f11Require(t, err)
	if !reflect.DeepEqual(loaded, &effective) || !reflect.DeepEqual(f11Entries(t, db), persisted) {
		t.Fatal("cold restart did not retain the same persisted configuration")
	}
}

func TestF11FreshInitialization(t *testing.T) {
	cases := []struct {
		name      string
		custom    bool
		schedule  *big.Int
		wrongID   bool
		wantError string
	}{
		{"valid_mainnet", false, nil, false, ""},
		{"conflicting_mainnet", false, big.NewInt(101), false, "suicide time-lock fix: mainnet activation differs from this build"},
		{"wrong_identity", false, nil, true, "suicide time-lock fix: mainnet chain identity mismatch"},
		{"negative_custom", true, big.NewInt(-1), false, "suicide time-lock fix: activation height must fit uint64"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f11MainnetSchedule(t, true)
			db := &f11ObservedDatabase{Database: rawdb.NewMemoryDatabase()}
			t.Cleanup(func() { db.Close() })
			genesis := f11Genesis(tc.custom, tc.schedule)
			if tc.wrongID {
				genesis.Config.ChainID = big.NewInt(1)
			}
			before := f11Entries(t, db)

			config, hash, err := core.SetupGenesisBlock(db, genesis)
			after := f11Entries(t, db)

			if tc.wantError != "" {
				if err == nil || err.Error() != tc.wantError || db.writes != 0 || !reflect.DeepEqual(before, after) {
					t.Fatalf("initialization rejection = %v, writes=%d", err, db.writes)
				}
				return
			}
			if err != nil || hash != params.MainnetGenesisHash || config == nil || !reflect.DeepEqual(config.SuicideTimeLockFixBlock, big.NewInt(100)) || rawdb.ReadChainConfig(db, hash) == nil {
				t.Fatalf("initialization = %v, %s, %v", config, hash, err)
			}
		})
	}
}

func TestF11ApprovalConfigurationBinding(t *testing.T) {
	f11MainnetSchedule(t, true)
	chainPath := filepath.Join(t.TempDir(), "chain")
	db := f11Open(t, chainPath, false)
	genesis := core.DefaultGenesisBlock()
	genesis.Config = &params.ChainConfig{ChainID: big.NewInt(32659), DaTong: &params.DaTongConfig{Period: 15}}
	f11SeedHead(t, db, genesis, 99)
	before := f11Entries(t, db)
	reader, err := NewReader(db)
	f11Require(t, err)
	actualJSON, err := json.Marshal(reader.Config())
	f11Require(t, err)
	actualHash, err := ConfigurationSHA256(reader.Config())
	f11Require(t, err)
	if string(actualJSON) != f11ExpectedConfigJSON || actualHash != common.HexToHash(f11ExpectedConfigSHA256) {
		t.Fatalf("effective config differs from independent JSON/hash vector: %s %s", actualJSON, actualHash)
	}
	executable, err := ExecutableSHA256()
	f11Require(t, err)
	signer := common.HexToAddress("0x01")
	owner := common.HexToAddress("0x02")
	policy := SigningPolicy{FirstParent: reader.CurrentHeader().Hash(), FirstParentNumber: 99, PurchaseOwner: owner, BlockCount: 1, ExecutableSHA256: executable, ConfigSHA256: common.HexToHash(f11ExpectedConfigSHA256)}
	approval := SigningApproval{Version: 1, Policy: policy, Plan: Plan{GenesisHash: params.MainnetGenesisHash, ChainID: 32659, ParentHash: policy.FirstParent, ParentNumber: 99, Signer: signer, Purchase: Purchase{Owner: owner}}}
	f11Require(t, checkApprovalContext(reader, &approval))
	f11Require(t, db.Close())
	identity := SigningIdentity{GenesisHash: params.MainnetGenesisHash, ChainID: 32659, Signer: signer}
	for _, tc := range []struct {
		name string
		hash string
	}{
		{"legacy_schedule", f11LegacyConfigSHA256},
		{"different_schedule", f11DifferentConfigSHA256},
	} {
		t.Run(tc.name, func(t *testing.T) {
			bad := approval
			bad.Policy.ConfigSHA256 = common.HexToHash(tc.hash)
			journalPath := filepath.Join(t.TempDir(), "journal")
			journal, err := CreateApprovedSigningJournal(journalPath, identity, bad.Policy)
			f11Require(t, err)
			f11Require(t, journal.Close())
			encoded, err := EncodeSigningApproval(bad)
			f11Require(t, err)
			calls := 0

			block, err := signApprovedOffline(chainPath, journalPath, encoded, common.Hash(sha256.Sum256(encoded)), func(accounts.Account, []byte) (*signingSession, error) {
				calls++
				return nil, fmt.Errorf("signer must not be opened")
			})

			if err == nil || err.Error() != "executable or chain configuration differs from approved policy" || calls != 0 || block != nil {
				t.Fatalf("approval rejection = %v, signer opens=%d, block=%v", err, calls, block)
			}
		})
	}
	db = f11Open(t, chainPath, true)
	defer db.Close()
	if !reflect.DeepEqual(f11Entries(t, db), before) {
		t.Fatal("approval validation changed the chain database")
	}
}

func f11MainnetSchedule(t *testing.T, enabled bool) {
	t.Helper()
	previous := params.MainnetChainConfig
	copy := *previous
	copy.RestartAnchor = nil
	copy.SuicideTimeLockFixBlock = nil
	if enabled {
		copy.SuicideTimeLockFixBlock = big.NewInt(100)
	}
	params.MainnetChainConfig = &copy
	t.Cleanup(func() { params.MainnetChainConfig = previous })
}

func f11Genesis(custom bool, schedule *big.Int) *core.Genesis {
	genesis := core.DefaultGenesisBlock()
	copy := *params.MainnetChainConfig
	copy.SuicideTimeLockFixBlock = schedule
	genesis.Config = &copy
	if custom {
		genesis.Nonce = 42
	}
	return genesis
}

func f11SeedHead(t *testing.T, db ethdb.Database, genesis *core.Genesis, height uint64) {
	t.Helper()
	block, err := genesis.Commit(db)
	f11Require(t, err)
	if genesis.Nonce != 42 && block.Hash() != params.MainnetGenesisHash {
		t.Fatalf("fixture genesis does not match mainnet identity: %s", block.Hash())
	}
	if height != 0 {
		header := &types.Header{Number: new(big.Int).SetUint64(height), ParentHash: block.Hash(), Root: block.Root(), Difficulty: big.NewInt(1), GasLimit: block.GasLimit(), Time: block.Time() + height}
		block = types.NewBlockWithHeader(header)
		rawdb.WriteBlock(db, block)
		rawdb.WriteCanonicalHash(db, block.Hash(), height)
		rawdb.WriteHeadBlockHash(db, block.Hash())
		rawdb.WriteHeadHeaderHash(db, block.Hash())
	}
	rawdb.WriteHeadFastBlockHash(db, block.Hash())
}

func f11Entries(t *testing.T, db ethdb.Database) map[string]string {
	t.Helper()
	entries := make(map[string]string)
	iterator := db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		entries[string(bytes.Clone(iterator.Key()))] = string(bytes.Clone(iterator.Value()))
	}
	f11Require(t, iterator.Error())
	return entries
}

func f11Open(t *testing.T, path string, readonly bool) ethdb.Database {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "f11-integration", readonly)
	f11Require(t, err)
	return db
}

func f11Require(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}
