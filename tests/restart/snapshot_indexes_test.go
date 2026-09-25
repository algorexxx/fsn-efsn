package restart

import (
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"sort"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/bitutil"
	"github.com/FusionFoundation/efsn/v5/core/bloombits"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/recovery"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/trie"
)

func TestSnapshotIndexInventory(t *testing.T) {
	output := os.Getenv("FUSION_RESTART_SNAPSHOT_INDEX_OUTPUT")
	if output == "" {
		t.Skip("requires explicit saved-backup or restored-database read-only inspection")
	}
	if !filepath.IsAbs(output) {
		t.Fatal("absolute new output path required")
	}
	backup := openInspectionBackup(t)
	reader, err := recovery.NewReader(backup.db)
	requireNoError(t, err)
	state, err := reader.StateAt(backup.head.Root, backup.head.MixDigest)
	requireNoError(t, err)
	tickets, err := state.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTickets() != 491 {
		t.Fatal("preserved ticket inventory differs")
	}
	heights := map[uint64]bool{0: true, 1: true, 2680000: true, 2700000: true, backup.head.Number.Uint64() - 256: true}
	for i := uint64(1); i <= 64; i++ {
		heights[backup.head.Number.Uint64()*i/64] = true
	}
	ordered := make([]uint64, 0, len(heights))
	for height := range heights {
		ordered = append(ordered, height)
	}
	sort.Slice(ordered, func(i, j int) bool { return ordered[i] < ordered[j] })
	lookups, missing := 0, make([]common.Hash, 0)
	for _, height := range ordered {
		hash := rawdb.ReadCanonicalHash(backup.db, height)
		block := rawdb.ReadBlock(backup.db, hash, height)
		if block == nil || block.Hash() != hash || types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() {
			t.Fatalf("missing or corrupt historical block %d", height)
		}
		receipts := rawdb.ReadReceipts(backup.db, hash, height, backup.config)
		if len(receipts) != len(block.Transactions()) || types.DeriveSha(receipts, trie.NewStackTrie(nil)) != block.ReceiptHash() || types.CreateBloom(receipts) != block.Bloom() {
			t.Fatalf("missing or corrupt historical receipts %d", height)
		}
		for i, tx := range block.Transactions() {
			if i != 0 && i != len(block.Transactions())-1 {
				continue
			}
			lookups++
			found, foundBlock, number, index := rawdb.ReadTransaction(backup.db, tx.Hash())
			if found == nil {
				missing = append(missing, tx.Hash())
				continue
			}
			if found.Hash() != tx.Hash() || foundBlock != hash || number != height || index != uint64(i) {
				t.Fatal("incorrect transaction lookup")
			}
			receipt, receiptBlock, receiptNumber, receiptIndex := rawdb.ReadReceipt(backup.db, tx.Hash(), backup.config)
			if receipt == nil || receipt.TxHash != tx.Hash() || receiptBlock != hash || receiptNumber != height || receiptIndex != uint64(i) {
				t.Fatal("incorrect receipt lookup")
			}
		}
	}
	index := rawdb.NewTable(backup.db, string(rawdb.BloomBitsIndexPrefix))
	count, err := index.Get([]byte("count"))
	requireNoError(t, err)
	if len(count) != 8 {
		t.Fatal("invalid bloom index count")
	}
	sections := binary.BigEndian.Uint64(count)
	expectedSections := (backup.head.Number.Uint64() + 1 - params.BloomConfirms) / params.BloomBitsBlocks
	if sections != expectedSections || sections == 0 {
		t.Fatalf("bloom coverage needs attention: stored=%d expected=%d", sections, expectedSections)
	}
	for section := uint64(0); section < sections; section++ {
		var encoded [8]byte
		binary.BigEndian.PutUint64(encoded[:], section)
		stored, err := index.Get(append([]byte("shead"), encoded[:]...))
		requireNoError(t, err)
		if common.BytesToHash(stored) != rawdb.ReadCanonicalHash(backup.db, (section+1)*params.BloomBitsBlocks-1) {
			t.Fatal("bloom section head mismatch")
		}
	}
	for _, section := range []uint64{0, sections - 1} {
		generator, err := bloombits.NewGenerator(uint(params.BloomBitsBlocks))
		requireNoError(t, err)
		for offset := uint64(0); offset < params.BloomBitsBlocks; offset++ {
			height := section*params.BloomBitsBlocks + offset
			header := rawdb.ReadHeader(backup.db, rawdb.ReadCanonicalHash(backup.db, height), height)
			if header == nil {
				t.Fatal("indexed header missing")
			}
			requireNoError(t, generator.AddBloom(uint(offset), header.Bloom))
		}
		head := rawdb.ReadCanonicalHash(backup.db, (section+1)*params.BloomBitsBlocks-1)
		for bit := uint(0); bit < types.BloomBitLength; bit++ {
			compressed, err := rawdb.ReadBloomBits(backup.db, bit, section, head)
			requireNoError(t, err)
			actual, err := bitutil.DecompressBytes(compressed, int(params.BloomBitsBlocks/8))
			requireNoError(t, err)
			expected, err := generator.Bitset(bit)
			requireNoError(t, err)
			if !bytes.Equal(actual, expected) {
				t.Fatal("bloom vector differs from canonical headers")
			}
		}
		t.Logf("reconstructed all bloom vectors for section=%d", section)
	}
	requireNoError(t, state.Error())
	report := map[string]interface{}{"head": backup.head.Hash(), "root": backup.head.Root, "ticket_root": backup.head.MixDigest, "tickets": tickets.NumberOfTickets(), "sampled_heights": ordered, "transaction_lookups": lookups, "missing_transaction_lookups": missing, "bloom_sections": sections, "checked_bloom_section_heads": sections, "reconstructed_bloom_sections": []uint64{0, sections - 1}, "scope": "Sampled historical blocks/receipts/transaction indexes; every bloom section head; first and last complete bloom sections; current ticket state. Not full historical execution or exhaustive transaction-index validation."}
	requireNoError(t, writeStateExportJSON(output, report))
	t.Logf("read-only snapshot inventory: sampled blocks=%d tx lookups=%d missing=%d bloom sections=%d", len(ordered), lookups, len(missing), sections)
}
