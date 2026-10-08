package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/ethdb"
	"github.com/FusionFoundation/efsn/v5/rlp"
)

var heights = []uint64{0, 1, 2, 1000, 1000000, 1000001, 2679999, 2680000, 2680001, 3599999, 3600000, 5799999, 5800000, 5800001, 8249999, 8250000, 8250001, 10000000, 12000000, 14000000, 15129952, 15129953, 15130079, 15130080}

type vector struct {
	Height          uint64
	Header          *types.Header
	Available       bool
	StorageKey      string
	CompressedBytes int
	PayloadBytes    int
	Owners          int
	Tickets         int
}

type comparison struct {
	Height            uint64
	ExactBytes        bool
	Commitment        common.Hash
	CommitmentMatches bool
	CacheError        string
	CompressedBytes   int
}

type observation struct {
	Genesis *types.Header
	Vectors []comparison
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	if len(os.Args) != 4 {
		return fmt.Errorf("usage: probe export DATABASE OUTPUT | compare VECTORS OUTPUT")
	}
	if os.Args[1] == "export" {
		return exportVectors(os.Args[2], os.Args[3])
	}
	if os.Args[1] == "compare" {
		return compareVectors(os.Args[2], os.Args[3])
	}
	return fmt.Errorf("unknown mode")
}

func exportVectors(directory, output string) error {
	db, err := rawdb.NewLevelDBDatabase(directory, 64, 64, "f12-readonly", true)
	if err != nil {
		return err
	}
	defer db.Close()
	genesis := common.HexToHash("0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a")
	head := common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f")
	if rawdb.ReadCanonicalHash(db, 0) != genesis || rawdb.ReadHeadBlockHash(db) != head || rawdb.ReadCanonicalHash(db, 15130080) != head {
		return fmt.Errorf("preserved genesis or head identity mismatch")
	}
	if err := os.Mkdir(output, 0755); err != nil {
		return err
	}
	vectors := make([]vector, 0, len(heights))
	for _, height := range heights {
		hash := rawdb.ReadCanonicalHash(db, height)
		header := rawdb.ReadHeader(db, hash, height)
		if header == nil || header.Hash() != hash || header.Number.Uint64() != height {
			return fmt.Errorf("missing or inconsistent header at %d", height)
		}
		v := vector{Height: height, Header: header}
		blob, key, err := readTicketBlob(db, header.MixDigest)
		if err != nil {
			return err
		}
		if blob == nil {
			vectors = append(vectors, v)
			continue
		}
		if len(blob) > 8*1024*1024 || crypto.Keccak256Hash(blob) != header.MixDigest {
			return fmt.Errorf("invalid or oversized ticket blob at %d", height)
		}
		payload, tickets, err := decodeTickets(blob)
		if err != nil {
			return fmt.Errorf("height %d: %w", height, err)
		}
		v.Available, v.StorageKey = true, key
		v.CompressedBytes, v.PayloadBytes, v.Owners = len(blob), len(payload), len(tickets)
		for _, owner := range tickets {
			v.Tickets += len(owner.Tickets)
		}
		if err := os.WriteFile(filepath.Join(output, fmt.Sprintf("%d.gz", height)), blob, 0644); err != nil {
			return err
		}
		if err := os.WriteFile(filepath.Join(output, fmt.Sprintf("%d.rlp", height)), payload, 0644); err != nil {
			return err
		}
		vectors = append(vectors, v)
	}
	encoded, err := json.MarshalIndent(vectors, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(output, "index.json"), append(encoded, '\n'), 0644); err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(vectors)
}

func readTicketBlob(db ethdb.KeyValueReader, hash common.Hash) ([]byte, string, error) {
	for _, key := range [][]byte{hash[:], append([]byte{'c'}, hash[:]...)} {
		has, err := db.Has(key)
		if err != nil {
			return nil, "", err
		}
		if !has {
			continue
		}
		blob, err := db.Get(key)
		if err != nil {
			return nil, "", err
		}
		if len(blob) == 0 {
			continue
		}
		return blob, fmt.Sprintf("%x", key), nil
	}
	return nil, "", nil
}

func decodeTickets(blob []byte) ([]byte, common.TicketsDataSlice, error) {
	reader, err := gzip.NewReader(bytes.NewReader(blob))
	if err != nil {
		return nil, nil, err
	}
	defer reader.Close()
	payload, err := io.ReadAll(io.LimitReader(reader, 16*1024*1024+1))
	if err != nil {
		return nil, nil, err
	}
	if len(payload) > 16*1024*1024 {
		return nil, nil, fmt.Errorf("ticket RLP limit exceeded")
	}
	var tickets common.TicketsDataSlice
	if err := rlp.DecodeBytes(payload, &tickets); err != nil {
		return nil, nil, err
	}
	reencoded, err := rlp.EncodeToBytes(&tickets)
	if err != nil {
		return nil, nil, err
	}
	if !bytes.Equal(payload, reencoded) {
		return nil, nil, fmt.Errorf("ticket RLP roundtrip differs")
	}
	return payload, tickets, nil
}

func compareVectors(input, output string) error {
	encoded, err := os.ReadFile(filepath.Join(input, "index.json"))
	if err != nil {
		return err
	}
	var vectors []vector
	if err := json.Unmarshal(encoded, &vectors); err != nil {
		return err
	}
	if err := os.Mkdir(output, 0755); err != nil {
		return err
	}
	db := rawdb.NewMemoryDatabase()
	defer db.Close()
	result := observation{Genesis: core.DefaultGenesisBlock().ToBlock(db).Header()}
	for _, v := range vectors {
		if !v.Available {
			continue
		}
		original, err := os.ReadFile(filepath.Join(input, fmt.Sprintf("%d.gz", v.Height)))
		if err != nil {
			return err
		}
		payload, tickets, err := decodeTickets(original)
		if err != nil {
			return err
		}
		var buffer bytes.Buffer
		writer := gzip.NewWriter(&buffer)
		if _, err := writer.Write(payload); err != nil {
			return err
		}
		if err := writer.Close(); err != nil {
			return err
		}
		compressed := buffer.Bytes()
		c := comparison{Height: v.Height, ExactBytes: bytes.Equal(original, compressed), Commitment: crypto.Keccak256Hash(compressed), CompressedBytes: len(compressed)}
		c.CommitmentMatches = c.Commitment == v.Header.MixDigest
		if err := state.AddCachedTickets(v.Header.MixDigest, tickets); err != nil {
			c.CacheError = err.Error()
		}
		if err := os.WriteFile(filepath.Join(output, fmt.Sprintf("%d.gz", v.Height)), compressed, 0644); err != nil {
			return err
		}
		result.Vectors = append(result.Vectors, c)
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
