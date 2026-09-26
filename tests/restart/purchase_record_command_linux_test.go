package restart

import (
	"bytes"
	"context"
	"crypto/sha256"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

func TestRestartPurchaseRecordCommand(t *testing.T) {
	requirePartitionNamespace(t)
	if !filepath.IsAbs(os.Getenv("FUSION_RESTART_EFSN_COMMAND")) {
		t.Fatal("requires the explicit absolute path to the tested efsn command")
	}
	directory := t.TempDir()
	path := filepath.Join(directory, "efsn", "chaindata")
	db, err := rawdb.NewLevelDBDatabase(path, 16, 16, "", false)
	if err != nil {
		t.Fatal(err)
	}
	body, err := rlp.EncodeToBytes(&common.BuyTicketParam{Start: 1, End: common.TimeLockForever})
	if err != nil {
		t.Fatal(err)
	}
	payload, err := rlp.EncodeToBytes(&common.FSNCallParam{Func: common.BuyTicketFunc, Data: body})
	if err != nil {
		t.Fatal(err)
	}
	key, err := crypto.HexToECDSA("0000000000000000000000000000000000000000000000000000000000000001")
	if err != nil {
		t.Fatal(err)
	}
	tx, err := types.SignTx(types.NewTransaction(17, common.FSNCallAddress, new(big.Int), 100000, big.NewInt(1000000000), payload), types.NewEIP155Signer(big.NewInt(55555)), key)
	if err != nil {
		t.Fatal(err)
	}
	encoded, err := tx.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}
	recordKey := common.FromHex("0x66736e2d6175746f2d7469636b65742d76312d7e5f4552091a69125d5dfcb7b8c2659029395bdf")
	if err := db.Put(recordKey, encoded); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	before := purchaseDatabaseFiles(t, path)
	command := runPurchaseDBGet(t, directory, fmt.Sprintf("%#x", recordKey))
	if command.err != nil || !bytes.Equal(command.output, []byte(fmt.Sprintf("key %#x: %#x\n", recordKey, encoded))) || !reflect.DeepEqual(before, purchaseDatabaseFiles(t, path)) {
		t.Fatalf("read-only purchase extraction failed or changed database files: %v output=%q", command.err, command.output)
	}
	absent := runPurchaseDBGet(t, directory, "0x00")
	if absent.err == nil || !reflect.DeepEqual(before, purchaseDatabaseFiles(t, path)) {
		t.Fatal("absent record was not rejected without changing database files")
	}
	db, err = rawdb.NewLevelDBDatabase(path, 16, 16, "", false)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	locked := runPurchaseDBGet(t, directory, fmt.Sprintf("%#x", recordKey))
	if locked.err == nil {
		t.Fatal("purchase extraction bypassed the open database lock")
	}
	after, err := db.Get(recordKey)
	if err != nil || !bytes.Equal(after, encoded) {
		t.Fatal("locked extraction changed the saved record")
	}
	t.Logf("existing db get preserved exact signed purchase nonce=17 hash=%s and all database file hashes; missing record and locked database rejected", tx.Hash().Hex())
}

func purchaseDatabaseFiles(t *testing.T, root string) map[string][32]byte {
	t.Helper()
	files := make(map[string][32]byte)
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		data, err := os.ReadFile(path)
		if err == nil {
			files[path] = sha256.Sum256(data)
		}
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	return files
}

type purchaseCommandResult struct {
	output []byte
	err    error
}

func runPurchaseDBGet(t *testing.T, directory, key string) purchaseCommandResult {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, os.Getenv("FUSION_RESTART_EFSN_COMMAND"), "--datadir", directory, "--syncmode", "full", "db", "get", key)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	output, err := cmd.Output()
	t.Logf("db get result=%v stderr=%s", err, stderr.Bytes())
	if ctx.Err() != nil || bytes.Contains(stderr.Bytes(), []byte("WARNING: DATA RACE")) {
		t.Fatal("db get timed out or reported a data race")
	}
	return purchaseCommandResult{output: output, err: err}
}
