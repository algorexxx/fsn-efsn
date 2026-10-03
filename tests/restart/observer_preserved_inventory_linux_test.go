package restart

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"strconv"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/state"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
	"golang.org/x/sys/unix"
)

type preservedInventoryBackend struct {
	ethapi.Backend
	chain inspectionChain
	state state.Database
}

func (backend *preservedInventoryBackend) StateAndHeaderByNumber(ctx context.Context, number rpc.BlockNumber) (*state.StateDB, *types.Header, error) {
	if err := ctx.Err(); err != nil {
		return nil, nil, err
	}
	if number < 0 {
		return nil, nil, fmt.Errorf("preserved inventory probe requires an explicit block height")
	}
	header := backend.chain.GetHeaderByNumber(uint64(number))
	if header == nil {
		return nil, nil, fmt.Errorf("header not found")
	}
	statedb, err := state.New(header.Root, header.MixDigest, backend.state)
	return statedb, header, err
}

type preservedInventoryRead struct {
	Wallet         common.Address
	Duration       time.Duration
	AllocatedBytes uint64
	JSONBytes      int
	Error          string
	Tickets        map[common.Hash]common.TicketDisplay
}

type preservedInventoryResult struct {
	Header              *types.Header
	BackupHead          common.Hash
	DatabaseOpen        time.Duration
	TicketCacheWasEmpty bool
	Reads               []preservedInventoryRead
	StateError          string
	TicketBlobBytes     int
	TicketBlobHash      common.Hash
	AllTickets          uint64
	Owners              uint64
	MatchedSavedHead    bool
}

func TestPreservedHistoricalInventory(t *testing.T) {
	output := os.Getenv("FUSION_RESTART_INVENTORY_OUTPUT")
	if output == "" {
		t.Skip("set FUSION_RESTART_INVENTORY_OUTPUT and FUSION_RESTART_INVENTORY_HEIGHT for a bounded read-only inventory probe")
	}
	height, err := strconv.ParseUint(os.Getenv("FUSION_RESTART_INVENTORY_HEIGHT"), 10, 64)
	requireNoError(t, err)
	if !filepath.IsAbs(output) {
		t.Fatal("inventory output must be an absolute new file")
	}
	var mount unix.Statfs_t
	requireNoError(t, unix.Statfs(os.Getenv("FUSION_RESTART_CHAINDATA"), &mount))
	if mount.Flags&unix.ST_RDONLY == 0 {
		t.Fatal("inventory probe requires a read-only source mount")
	}
	started := time.Now()
	backup := openInspectionBackup(t)
	result := preservedInventoryResult{BackupHead: backup.head.Hash(), DatabaseOpen: time.Since(started)}
	if height > backup.head.Number.Uint64() {
		t.Fatal("inventory height exceeds preserved head")
	}
	backend := &preservedInventoryBackend{chain: inspectionChain{backup}, state: state.NewDatabase(backup.db)}
	result.Header = backend.chain.GetHeaderByNumber(height)
	if result.Header == nil {
		t.Fatal("missing preserved header")
	}
	result.TicketCacheWasEmpty = state.GetCachedTickets(result.Header.MixDigest) == nil
	if !result.TicketCacheWasEmpty {
		t.Fatal("run each height in a fresh process before any ticket lookup")
	}
	api := ethapi.NewPublicFusionAPI(backend)
	owners := []common.Address{
		common.HexToAddress("0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1"),
		common.HexToAddress("0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a"),
		common.HexToAddress("0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1"),
	}
	for _, owner := range owners {
		result.Reads = append(result.Reads, measurePreservedInventory(api, owner, height))
	}
	statedb, _, stateErr := backend.StateAndHeaderByNumber(context.Background(), rpc.BlockNumber(height))
	var all common.TicketsDataSlice
	if stateErr == nil {
		blob := statedb.GetData(common.TicketKeyAddress)
		stateErr = statedb.Error()
		if stateErr == nil {
			result.TicketBlobBytes, result.TicketBlobHash = len(blob), crypto.Keccak256Hash(blob)
			if result.TicketBlobHash != result.Header.MixDigest {
				t.Fatal("stored ticket blob differs from header commitment")
			}
			reader, err := gzip.NewReader(bytes.NewReader(blob))
			requireNoError(t, err)
			decoded, err := io.ReadAll(reader)
			requireNoError(t, err)
			requireNoError(t, reader.Close())
			requireNoError(t, rlp.DecodeBytes(decoded, &all))
			result.AllTickets, result.Owners = all.NumberOfTicketsAndOwners()
		}
	}
	if stateErr != nil {
		result.StateError = stateErr.Error()
	}
	for _, read := range result.Reads {
		if stateErr != nil {
			if read.Error == "" || read.Tickets != nil {
				t.Fatal("unavailable state was reported as a successful inventory")
			}
			continue
		}
		var expected map[common.Hash]common.TicketDisplay
		for _, entry := range all {
			if entry.Owner == read.Wallet {
				expected = entry.ToMap()
			}
		}
		if read.Error != "" || !reflect.DeepEqual(read.Tickets, expected) {
			t.Fatal("API inventory differs from the independently read committed blob")
		}
	}
	if height == backup.head.Number.Uint64() {
		var expected map[common.Hash]common.TicketDisplay
		requireNoError(t, json.Unmarshal(readRPCObservations(t)[7], &expected))
		if stateErr != nil || !reflect.DeepEqual(all.ToMap(), expected) {
			t.Fatal("preserved head inventory differs from the saved gateway observation")
		}
		result.MatchedSavedHead = true
	}
	for _, hash := range []common.Hash{rawdb.ReadHeadHeaderHash(backup.db), rawdb.ReadHeadBlockHash(backup.db), rawdb.ReadHeadFastBlockHash(backup.db)} {
		if hash != backup.head.Hash() {
			t.Fatal("preserved head pointers differ")
		}
	}
	requireNoError(t, writeStateExportJSON(output, result))
	t.Logf("height=%d tickets=%d owners=%d firstRead=%s repeatRead=%s stateError=%q", height, result.AllTickets, result.Owners, result.Reads[0].Duration, result.Reads[2].Duration, result.StateError)
}

func measurePreservedInventory(api *ethapi.PublicFusionAPI, owner common.Address, height uint64) preservedInventoryRead {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	started := time.Now()
	tickets, err := api.AllTicketsByAddress(ctx, owner, rpc.BlockNumber(height))
	result := preservedInventoryRead{Wallet: owner, Duration: time.Since(started), Tickets: tickets}
	runtime.ReadMemStats(&after)
	result.AllocatedBytes = after.TotalAlloc - before.TotalAlloc
	if err != nil {
		result.Error = err.Error()
	}
	encoded, _ := json.Marshal(tickets)
	result.JSONBytes = len(encoded)
	return result
}
