package restart

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func TestFullStateKeyAudit(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_FULL_STATE_AUDIT")
	if directory == "" {
		t.Skip("set FUSION_RESTART_FULL_STATE_AUDIT to inspect the verified state read-only")
	}
	if !filepath.IsAbs(directory) {
		t.Fatal("absolute state path required")
	}
	encoded, err := os.ReadFile(filepath.Join(directory, "identity.json"))
	requireNoError(t, err)
	var identity stateExportIdentity
	requireNoError(t, json.Unmarshal(encoded, &identity))
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 128, 64, "full-state-audit", true)
	requireNoError(t, err)
	defer db.Close()
	statedb, err := state.New(identity.Head.Root, identity.Head.MixDigest, state.NewDatabase(db))
	requireNoError(t, err)
	key := make([]byte, 32)
	key[31] = 1
	private, err := crypto.ToECDSA(key)
	requireNoError(t, err)
	for _, address := range []common.Address{common.HexToAddress("0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1"), crypto.PubkeyToAddress(private.PublicKey)} {
		data, err := json.Marshal(struct {
			Address  common.Address
			Exists   bool
			Nonce    uint64
			Balances map[common.Hash]string
			Locks    map[common.Hash]*common.TimeLock
			CodeHash common.Hash
		}{address, statedb.Exist(address), statedb.GetNonce(address), statedb.GetAllBalances(address), statedb.GetAllTimeLockBalances(address), statedb.GetCodeHash(address)})
		requireNoError(t, err)
		t.Log(string(data))
	}
	requireNoError(t, statedb.Error())
}
