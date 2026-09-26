package restart

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/params"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/trie"
	"golang.org/x/sys/unix"
)

type fullStateHistoryIdentity struct {
	Head       *types.Header
	Previous   *types.Header
	PreviousTD *big.Int
	HeadTD     *big.Int
}

type fullStateHistoryResult struct {
	First        uint64
	Last         uint64
	Blocks       uint64
	Transactions uint64
	Bytes        uint64
	SHA256       string
}

func TestExportFullStateHistory(t *testing.T) {
	path := os.Getenv("FUSION_RESTART_HISTORY_OUTPUT")
	if path == "" {
		t.Skip("requires read-only preserved backup and new history output")
	}
	if !filepath.IsAbs(path) {
		t.Fatal("absolute history output required")
	}
	backup := openInspectionBackup(t)
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(os.Getenv("FUSION_RESTART_CHAINDATA"), &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("history extraction requires read-only source mount")
	}
	first := backup.head.Number.Uint64() - params.FullImmutabilityThreshold
	previous := rawdb.ReadHeader(backup.db, rawdb.ReadCanonicalHash(backup.db, first-1), first-1)
	if previous == nil {
		t.Fatal("missing initial history header")
	}
	identity := fullStateHistoryIdentity{Head: &backup.head, Previous: previous, PreviousTD: rawdb.ReadTd(backup.db, previous.Hash(), first-1), HeadTD: rawdb.ReadTd(backup.db, backup.head.Hash(), backup.head.Number.Uint64())}
	if identity.PreviousTD == nil || identity.HeadTD == nil {
		t.Fatal("missing history difficulty")
	}
	var output io.Writer = io.Discard
	var file *os.File
	mode := os.Getenv("FUSION_RESTART_HISTORY_MODE")
	if mode == "export" {
		requireReplaySpace(t, filepath.Dir(path))
		var err error
		file, err = os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		requireNoError(t, err)
		defer file.Close()
		output = file
	} else if mode != "measure" {
		t.Fatal("history mode must be measure or export")
	}
	hash := sha256.New()
	output = io.MultiWriter(output, hash)
	encoded, err := rlp.EncodeToBytes(identity)
	requireNoError(t, err)
	_, err = output.Write(encoded)
	requireNoError(t, err)
	result := fullStateHistoryResult{First: first, Last: backup.head.Number.Uint64(), Bytes: uint64(len(encoded))}
	td := new(big.Int).Set(identity.PreviousTD)
	last := time.Now()
	for height := first; height <= result.Last; height++ {
		canonical := rawdb.ReadCanonicalHash(backup.db, height)
		block := rawdb.ReadBlock(backup.db, canonical, height)
		requireNoError(t, checkFullStateHistoryBlock(block, previous))
		td.Add(td, block.Difficulty())
		storedTD := rawdb.ReadTd(backup.db, canonical, height)
		if block.Hash() != canonical || storedTD == nil || storedTD.Cmp(td) != 0 {
			t.Fatalf("canonical identity or cumulative difficulty differs at %d", height)
		}
		encoded, err = rlp.EncodeToBytes(block)
		requireNoError(t, err)
		_, err = output.Write(encoded)
		requireNoError(t, err)
		result.Blocks++
		result.Transactions += uint64(len(block.Transactions()))
		result.Bytes += uint64(len(encoded))
		previous = block.Header()
		if time.Since(last) > 20*time.Second {
			t.Logf("history %s progress: blocks=%d bytes=%d height=%d", mode, result.Blocks, result.Bytes, height)
			last = time.Now()
			requireReplaySpace(t, filepath.Dir(path))
		}
	}
	if previous.Hash() != backup.head.Hash() || td.Cmp(identity.HeadTD) != 0 {
		t.Fatal("history did not reach preserved head")
	}
	if file != nil {
		requireNoError(t, file.Sync())
		requireNoError(t, file.Close())
	}
	result.SHA256 = hex.EncodeToString(hash.Sum(nil))
	requireNoError(t, writeStateExportJSON(path+"."+mode+".json", result))
	t.Logf("history %s complete: %+v head=%s td=%s executable=%s", mode, result, previous.Hash().Hex(), td, stateExportExecutableHash(t))
}

func checkFullStateHistoryBlock(block *types.Block, previous *types.Header) error {
	if block == nil || previous == nil || block.NumberU64() != previous.Number.Uint64()+1 || block.ParentHash() != previous.Hash() || block.Difficulty().Sign() <= 0 {
		return fmt.Errorf("missing or discontinuous historical block")
	}
	if types.DeriveSha(block.Transactions(), trie.NewStackTrie(nil)) != block.TxHash() || len(block.Uncles()) != 0 {
		return fmt.Errorf("historical block body commitment mismatch at %d", block.NumberU64())
	}
	return nil
}

func TestFullStateHistoryBodyValidation(t *testing.T) {
	parent := &types.Header{Number: big.NewInt(42)}
	header := &types.Header{Number: big.NewInt(43), ParentHash: parent.Hash(), Difficulty: big.NewInt(2), TxHash: types.EmptyRootHash, UncleHash: common.HexToHash("0x1234")}
	for _, damage := range []string{"none", "missing", "gap", "parent", "transaction", "uncle"} {
		t.Run(damage, func(t *testing.T) {
			copy := types.CopyHeader(header)
			block := types.NewBlockWithHeader(copy)
			switch damage {
			case "missing":
				block = nil
			case "gap":
				copy.Number = big.NewInt(44)
				block = types.NewBlockWithHeader(copy)
			case "parent":
				copy.ParentHash = common.Hash{}
				block = types.NewBlockWithHeader(copy)
			case "transaction":
				block = block.WithBody(types.Transactions{types.NewTransaction(0, common.Address{}, big.NewInt(1), 21000, big.NewInt(1), nil)}, nil)
			case "uncle":
				block = block.WithBody(nil, []*types.Header{parent})
			}
			err := checkFullStateHistoryBlock(block, parent)
			if damage == "none" {
				requireNoError(t, err)
			} else if err == nil {
				t.Fatal("accepted damaged historical block")
			}
		})
	}
}

func readFullStateHistory(t *testing.T, path string, visit func(*types.Block, *big.Int)) fullStateHistoryResult {
	t.Helper()
	file, err := os.Open(path)
	requireNoError(t, err)
	defer file.Close()
	hash := sha256.New()
	stream := rlp.NewStream(io.TeeReader(file, hash), 0)
	var identity fullStateHistoryIdentity
	requireNoError(t, stream.Decode(&identity))
	var context fullStateContext
	data, err := os.ReadFile("../../docs/evidence/restart-full-state-2026-09-24/context.rlp")
	requireNoError(t, err)
	requireNoError(t, rlp.DecodeBytes(data, &context))
	if identity.Head == nil || identity.Previous == nil || identity.PreviousTD == nil || identity.HeadTD == nil || identity.PreviousTD.Sign() <= 0 || identity.Head.Hash() != context.Parent.Hash() || identity.HeadTD.Cmp(context.TotalDifficulty) != 0 || identity.Previous.Number.Uint64()+params.FullImmutabilityThreshold+1 != identity.Head.Number.Uint64() {
		t.Fatal("history identity does not match trusted preserved context")
	}
	result := fullStateHistoryResult{First: identity.Previous.Number.Uint64() + 1, Last: identity.Head.Number.Uint64()}
	previous, td := identity.Previous, new(big.Int).Set(identity.PreviousTD)
	for number := result.First; number <= result.Last; number++ {
		var block *types.Block
		requireNoError(t, stream.Decode(&block))
		requireNoError(t, checkFullStateHistoryBlock(block, previous))
		td.Add(td, block.Difficulty())
		if visit != nil {
			visit(block, new(big.Int).Set(td))
		}
		result.Blocks++
		result.Transactions += uint64(len(block.Transactions()))
		previous = block.Header()
	}
	var extra types.Block
	if err := stream.Decode(&extra); err != io.EOF || previous.Hash() != identity.Head.Hash() || td.Cmp(identity.HeadTD) != 0 {
		t.Fatal("history ends incorrectly or has trailing data")
	}
	stat, err := file.Stat()
	requireNoError(t, err)
	result.Bytes, result.SHA256 = uint64(stat.Size()), hex.EncodeToString(hash.Sum(nil))
	return result
}

func installFullStateHistory(t *testing.T, root string) {
	t.Helper()
	path := os.Getenv("FUSION_RESTART_HISTORY_INPUT")
	if !filepath.IsAbs(path) {
		t.Fatal("partition requires an absolute genuine history segment")
	}
	verified := readFullStateHistory(t, path, nil)
	var exported fullStateHistoryResult
	readHandoverJSON(t, path+".export.json", &exported)
	if verified != exported {
		t.Fatal("history bytes differ from verified export")
	}
	for _, role := range []string{"producer", "verifier"} {
		if !t.Run("history-"+role, func(t *testing.T) {
			directory := filepath.Join(root, role)
			requireFullStateCopy(t, directory)
			f, original, _ := openFullStateHandover(t, directory)
			head := f.chain.CurrentBlock().Hash()
			batch := f.db.NewBatch()
			count := 0
			actual := readFullStateHistory(t, path, func(block *types.Block, td *big.Int) {
				if block.NumberU64() == original.Source.Number.Uint64() {
					if block.Hash() != original.Source.Hash() || block.ParentHash() != original.Parent.ParentHash {
						t.Fatal("history does not attach to audited synthetic parent")
					}
					return
				}
				stored := rawdb.ReadCanonicalHash(f.db, block.NumberU64())
				if stored != (common.Hash{}) && stored != block.Hash() {
					t.Fatal("history conflicts with an existing canonical header")
				}
				rawdb.WriteBlock(batch, block)
				rawdb.WriteTd(batch, block.Hash(), block.NumberU64(), td)
				rawdb.WriteCanonicalHash(batch, block.Hash(), block.NumberU64())
				count++
				if count%1000 == 0 {
					requireNoError(t, batch.Write())
					batch.Reset()
					requireReplaySpace(t, directory)
				}
			})
			requireNoError(t, batch.Write())
			if actual != verified || count != params.FullImmutabilityThreshold || f.chain.CurrentBlock().Hash() != head || rawdb.ReadHeadBlockHash(f.db) != head || rawdb.ReadHeadHeaderHash(f.db) != head || rawdb.ReadHeadFastBlockHash(f.db) != head {
				t.Fatal("history install changed the active head or source identity")
			}
			requireNoError(t, writeStateExportJSON(filepath.Join(directory, "history-installed.json"), verified))
			t.Logf("genuine ancestry installed role=%s blocks=%d from=%d through=%d bytes=%d sha256=%s; audited parent and all heads unchanged", role, count, verified.First, verified.Last-1, verified.Bytes, verified.SHA256)
		}) {
			t.Fatal("history installation failed")
		}
	}
}
