package restart

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

type purchaseInventoryTransaction struct {
	Hash     common.Hash
	Owner    common.Address
	Nonce    uint64
	ChainID  string
	Purchase *common.BuyTicketParam `json:",omitempty"`
}

type purchaseInventoryWallet struct {
	Owner            common.Address
	CanonicalNonce   uint64
	AutomaticPresent bool
	Automatic        *purchaseInventoryTransaction `json:",omitempty"`
}

func TestBackupPurchaseInventory(t *testing.T) {
	directory := os.Getenv("FUSION_RESTART_PURCHASE_INVENTORY")
	if directory == "" {
		t.Skip("requires explicit stopped backup efsn directory")
	}
	output := os.Getenv("FUSION_RESTART_PURCHASE_INVENTORY_OUTPUT")
	if !filepath.IsAbs(directory) || !filepath.IsAbs(output) {
		t.Fatal("absolute backup directory and new report path required")
	}
	file, err := os.Open(filepath.Join(directory, "transactions.rlp"))
	requireNoError(t, err)
	data, err := io.ReadAll(io.LimitReader(file, (16<<20)+1))
	file.Close()
	requireNoError(t, err)
	if len(data) > 16<<20 {
		t.Fatal("transaction journal exceeds inventory size limit")
	}
	db, err := rawdb.NewLevelDBDatabase(filepath.Join(directory, "chaindata"), 128, 64, "purchase-inventory", true)
	requireNoError(t, err)
	defer db.Close()
	reader, err := recovery.NewReader(db)
	requireNoError(t, err)
	head := reader.CurrentHeader()
	if head.Hash() != common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f") {
		t.Fatal("inventory source is not the pinned preserved backup head")
	}
	state, err := reader.StateAt(head.Root, head.MixDigest)
	requireNoError(t, err)
	journal := make([]purchaseInventoryTransaction, 0)
	stream := rlp.NewStream(bytes.NewReader(data), uint64(len(data)))
	for {
		var tx types.Transaction
		if err := stream.Decode(&tx); err == io.EOF {
			break
		} else if err != nil {
			t.Fatal(err)
		}
		journal = append(journal, inspectPurchaseTransaction(t, &tx, types.LatestSigner(reader.Config())))
		if len(journal) > 10000 {
			t.Fatal("journal transaction limit exceeded")
		}
	}
	wallets := make([]purchaseInventoryWallet, 0, 2)
	for _, address := range []string{"0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1", "0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a"} {
		owner := common.HexToAddress(address)
		key := append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
		present, err := db.Has(key)
		requireNoError(t, err)
		wallet := purchaseInventoryWallet{Owner: owner, CanonicalNonce: state.GetNonce(owner), AutomaticPresent: present}
		if present {
			encoded, err := db.Get(key)
			requireNoError(t, err)
			var tx types.Transaction
			requireNoError(t, tx.UnmarshalBinary(encoded))
			transaction := inspectPurchaseTransaction(t, &tx, types.LatestSigner(reader.Config()))
			if transaction.Owner != owner || transaction.Purchase == nil {
				t.Fatal("automatic journal has wrong sender or payload")
			}
			wallet.Automatic = &transaction
		}
		wallets = append(wallets, wallet)
	}
	requireNoError(t, state.Error())
	digest := sha256.Sum256(data)
	report := struct {
		Directory     string
		Head          common.Hash
		Height        uint64
		JournalBytes  int
		JournalSHA256 string
		Transactions  []purchaseInventoryTransaction
		Wallets       []purchaseInventoryWallet
		Scope         string
	}{directory, head.Hash(), head.Number.Uint64(), len(data), hex.EncodeToString(digest[:]), journal, wallets, "Stopped saved backup only; excludes live pools, remote peers, startup configuration and private-key files."}
	requireNoError(t, writeStateExportJSON(output, report))
	t.Logf("saved backup inventory: height=%d journal bytes=%d transactions=%d wallets=%+v", report.Height, report.JournalBytes, len(journal), wallets)
}

func inspectPurchaseTransaction(t *testing.T, tx *types.Transaction, signer types.Signer) purchaseInventoryTransaction {
	t.Helper()
	owner, err := types.Sender(signer, tx)
	requireNoError(t, err)
	record := purchaseInventoryTransaction{Hash: tx.Hash(), Owner: owner, Nonce: tx.Nonce(), ChainID: tx.ChainId().String()}
	if tx.To() == nil || *tx.To() != common.FSNCallAddress {
		return record
	}
	var call common.FSNCallParam
	requireNoError(t, rlp.DecodeBytes(tx.Data(), &call))
	if call.Func == common.BuyTicketFunc {
		var purchase common.BuyTicketParam
		if err := rlp.DecodeBytes(call.Data, &purchase); err != nil {
			t.Fatal(fmt.Errorf("decode journal purchase %s: %w", tx.Hash().Hex(), err))
		}
		record.Purchase = &purchase
	}
	return record
}
