package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type f11CLIFixture struct {
	directory    string
	chain        string
	plan         recovery.Plan
	planPath     string
	purchasePath string
	reportPath   string
	before       map[string]string
}

func TestF11CLIReportAndPrepareConfiguration(t *testing.T) {
	for _, tc := range []struct {
		name       string
		stored     *big.Int
		registered bool
		approved   *big.Int
		vector     string
	}{
		{"legacy_resolved", nil, true, big.NewInt(100), "effective"},
		{"matching_stored", big.NewInt(100), true, big.NewInt(100), "effective"},
		{"unselected", nil, true, nil, "legacy"},
		{"custom_same_id", nil, false, big.NewInt(100), "legacy"},
		{"custom_schedule", big.NewInt(101), false, big.NewInt(100), "different"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			fixture := f11PrepareFixture(t, tc.stored, tc.registered, tc.approved)
			output := filepath.Join(fixture.directory, "approval.json")
			vector := f11ConfigVectors[tc.vector]

			reviewErr := runCommand(fixture.reviewArgs())
			f11Require(t, reviewErr)
			prepareErr := runCommand(fixture.prepareArgs(fixture.reportPath, output, "-blocks", "1"))
			f11Require(t, prepareErr)
			var reviewed report
			f11ReadJSON(t, fixture.reportPath, &reviewed)
			var approval recovery.SigningApproval
			f11ReadJSON(t, output, &approval)
			configJSON, err := json.Marshal(reviewed.ChainConfig)
			f11Require(t, err)
			executable, err := os.Executable()
			f11Require(t, err)
			binary, err := os.ReadFile(executable)
			f11Require(t, err)
			wantPolicy := recovery.SigningPolicy{FirstParent: fixture.plan.ParentHash, FirstParentNumber: 0, PurchaseOwner: fixture.plan.Purchase.Owner, BlockCount: 1, ExecutableSHA256: common.Hash(sha256.Sum256(binary)), ConfigSHA256: common.HexToHash(vector.SHA256)}

			if string(configJSON) != vector.JSON || approval.Policy != wantPolicy || !reflect.DeepEqual(approval.Plan, fixture.plan) {
				t.Fatalf("report/configuration approval mismatch: config=%s policy=%+v", configJSON, approval.Policy)
			}
			if !bytes.Equal(approval.UnsignedBlock, reviewed.UnsignedBlock) {
				t.Fatal("prepare changed the reviewed unsigned block")
			}
			f11CheckChainUnchanged(t, fixture)
		})
	}
}

func TestF11CLIRejectsChangedReportSchedule(t *testing.T) {
	fixture := f11PrepareFixture(t, nil, true, big.NewInt(100))
	f11Require(t, runCommand(fixture.reviewArgs()))
	for _, tc := range []struct {
		name   string
		height *big.Int
	}{
		{"removed", nil},
		{"changed", big.NewInt(101)},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var reviewed report
			f11ReadJSON(t, fixture.reportPath, &reviewed)
			reviewed.ChainConfig.SuicideTimeLockFixBlock = tc.height
			path := filepath.Join(fixture.directory, tc.name+"-report.json")
			f11WriteJSON(t, path, reviewed)
			output := filepath.Join(fixture.directory, tc.name+"-approval.json")

			err := runCommand(fixture.prepareArgs(path, output, "-blocks", "1"))

			f11CheckRejection(t, fixture, output, err, "report differs from the complete rebuilt canonical report")
		})
	}
}

func TestF11CLIPriorApprovalConfiguration(t *testing.T) {
	fixture := f11PrepareFixture(t, nil, true, big.NewInt(100))
	f11Require(t, runCommand(fixture.reviewArgs()))
	initial := filepath.Join(fixture.directory, "initial-approval.json")
	f11Require(t, runCommand(fixture.prepareArgs(fixture.reportPath, initial, "-blocks", "1")))
	for _, tc := range []struct {
		name      string
		vector    string
		wantError string
	}{
		{"matching", "effective", ""},
		{"legacy", "legacy", "prior approval identity or runtime differs from this report"},
		{"different", "different", "prior approval identity or runtime differs from this report"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var prior recovery.SigningApproval
			f11ReadJSON(t, initial, &prior)
			prior.Policy.ConfigSHA256 = common.HexToHash(f11ConfigVectors[tc.vector].SHA256)
			path := filepath.Join(fixture.directory, tc.name+"-prior.json")
			data := f11WriteJSON(t, path, prior)
			digest := common.Hash(sha256.Sum256(data))
			output := filepath.Join(fixture.directory, tc.name+"-next.json")

			err := runCommand(fixture.prepareArgs(fixture.reportPath, output, "-policy-from", path, "-policy-sha256", digest.Hex()))

			if tc.wantError != "" {
				f11CheckRejection(t, fixture, output, err, tc.wantError)
				return
			}
			f11Require(t, err)
			var next recovery.SigningApproval
			f11ReadJSON(t, output, &next)
			if !reflect.DeepEqual(next, prior) {
				t.Fatal("matching prior approval changed the approved first-stage context")
			}
			f11CheckChainUnchanged(t, fixture)
		})
	}
}

func TestF11CLIRejectsConflictingStoredSchedule(t *testing.T) {
	fixture := f11PrepareFixture(t, big.NewInt(101), true, big.NewInt(100))

	err := runCommand(fixture.reviewArgs())

	f11CheckRejection(t, fixture, fixture.reportPath, err, "suicide time-lock fix: mainnet activation differs from this build")
}

func f11PrepareFixture(t *testing.T, stored *big.Int, registered bool, approved *big.Int) *f11CLIFixture {
	t.Helper()
	directory := t.TempDir()
	chainPath := filepath.Join(directory, "chain")
	keyBytes := make([]byte, 32)
	keyBytes[31] = 2
	key, err := crypto.ToECDSA(keyBytes)
	f11Require(t, err)
	owner := crypto.PubkeyToAddress(key.PublicKey)
	signer := common.HexToAddress("0x01")
	config := &params.ChainConfig{ChainID: big.NewInt(32659), HomesteadBlock: big.NewInt(0), EIP155Block: big.NewInt(0), EIP158Block: big.NewInt(0), ByzantiumBlock: big.NewInt(0), DaTong: &params.DaTongConfig{Period: 15}, SuicideTimeLockFixBlock: stored}
	genesis := &core.Genesis{Config: config, Nonce: 1, GasLimit: 4700000, Difficulty: big.NewInt(1), Timestamp: 1700000000, TicketCreateInfo: &core.TicketsCreate{Owner: signer, Time: 1700000000, Count: 1}, Alloc: core.GenesisAlloc{owner: {Balance: new(big.Int).Mul(big.NewInt(10000), new(big.Int).Exp(big.NewInt(10), big.NewInt(18), nil))}}}
	db, err := rawdb.NewLevelDBDatabase(chainPath, 16, 16, "f11-cli-fixture", false)
	f11Require(t, err)
	parent, err := genesis.Commit(db)
	f11Require(t, err)
	rawdb.WriteHeadFastBlockHash(db, parent.Hash())
	f11Require(t, db.Close())
	previousConfig, previousHash := params.MainnetChainConfig, params.MainnetGenesisHash
	approvedConfig := *config
	approvedConfig.SuicideTimeLockFixBlock = approved
	params.MainnetChainConfig = &approvedConfig
	if registered {
		params.MainnetGenesisHash = parent.Hash()
	}
	t.Cleanup(func() { params.MainnetChainConfig, params.MainnetGenesisHash = previousConfig, previousHash })
	body, err := rlp.EncodeToBytes(&common.BuyTicketParam{Start: 1700000000, End: 1702592000})
	f11Require(t, err)
	data, err := rlp.EncodeToBytes(&common.FSNCallParam{Func: common.BuyTicketFunc, Data: body})
	f11Require(t, err)
	tx, err := types.SignTx(types.NewTransaction(0, common.FSNCallAddress, new(big.Int), 100000, big.NewInt(2000000000), data), types.NewEIP155Signer(big.NewInt(32659)), key)
	f11Require(t, err)
	purchase, err := rlp.EncodeToBytes(tx)
	f11Require(t, err)
	plan := recovery.Plan{GenesisHash: parent.Hash(), ChainID: 32659, ParentNumber: 0, ParentHash: parent.Hash(), Signer: signer, Timestamp: 1700000120, NextTimestamp: 1700000240, Purchase: recovery.Purchase{Hash: tx.Hash(), Owner: owner, Nonce: 0, Start: 1700000000, End: 1702592000}}
	fixture := &f11CLIFixture{directory: directory, chain: chainPath, plan: plan, planPath: filepath.Join(directory, "plan.json"), purchasePath: filepath.Join(directory, "purchase.rlp"), reportPath: filepath.Join(directory, "report.json")}
	f11WriteJSON(t, fixture.planPath, plan)
	f11Require(t, os.WriteFile(fixture.purchasePath, purchase, 0600))
	fixture.before = f11ReadChain(t, chainPath)
	return fixture
}

func (f *f11CLIFixture) reviewArgs() []string {
	return []string{"review", "-chaindata", f.chain, "-plan", f.planPath, "-purchase", f.purchasePath, "-out", f.reportPath}
}

func (f *f11CLIFixture) prepareArgs(reportPath, output string, mode ...string) []string {
	return append([]string{"prepare", "-chaindata", f.chain, "-report", reportPath, "-purchase", f.purchasePath, "-out", output}, mode...)
}

func f11ReadChain(t *testing.T, path string) map[string]string {
	t.Helper()
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "f11-cli-check", true)
	f11Require(t, err)
	defer db.Close()
	entries := make(map[string]string)
	iterator := db.NewIterator(nil, nil)
	defer iterator.Release()
	for iterator.Next() {
		entries[string(bytes.Clone(iterator.Key()))] = string(bytes.Clone(iterator.Value()))
	}
	f11Require(t, iterator.Error())
	return entries
}

func f11CheckChainUnchanged(t *testing.T, fixture *f11CLIFixture) {
	t.Helper()
	if !reflect.DeepEqual(f11ReadChain(t, fixture.chain), fixture.before) {
		t.Fatal("CLI changed chain key/value contents")
	}
}

func f11CheckRejection(t *testing.T, fixture *f11CLIFixture, output string, err error, want string) {
	t.Helper()
	if err == nil || err.Error() != want {
		t.Fatalf("rejection = %v; want %s", err, want)
	}
	if _, err := os.Stat(output); !os.IsNotExist(err) {
		t.Fatal("rejected command created an output file")
	}
	f11CheckChainUnchanged(t, fixture)
}

func f11ReadJSON(t *testing.T, path string, result interface{}) {
	t.Helper()
	data, err := os.ReadFile(path)
	f11Require(t, err)
	f11Require(t, json.Unmarshal(data, result))
}

func f11WriteJSON(t *testing.T, path string, value interface{}) []byte {
	t.Helper()
	data, err := json.MarshalIndent(value, "", "  ")
	f11Require(t, err)
	data = append(data, '\n')
	f11Require(t, os.WriteFile(path, data, 0600))
	return data
}

func f11Require(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}
