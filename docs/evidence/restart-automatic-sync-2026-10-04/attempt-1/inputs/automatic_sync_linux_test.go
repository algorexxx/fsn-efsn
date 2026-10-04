package restart

import (
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/core/rawdb"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
)

func rehearseUnknownHeavierAutomaticSync(t *testing.T) {
	pair := seedDenseMinerPairWithWindow(t, "1000000000000000000000000", 0, nil, 1700000000, 0)
	acceptedSeed, foreignSeed := pair.miners[0], pair.miners[1]
	shared := acceptedSeed.chain.CurrentBlock()
	accepted := roundTripBlocks(t, buildAnchorBranch(t, acceptedSeed, 4, 120))
	acceptedHead := accepted[len(accepted)-1]
	acceptedTD := acceptedSeed.chain.GetTd(acceptedHead.Hash(), acceptedHead.NumberU64())
	var foreign types.Blocks
	for len(foreign) < 12 {
		foreign = append(foreign, buildAnchorBranch(t, foreignSeed, 1, 121)...)
		head := foreignSeed.chain.CurrentBlock()
		if foreignSeed.chain.GetTd(head.Hash(), head.NumberU64()).Cmp(acceptedTD) > 0 {
			break
		}
	}
	foreign = roundTripBlocks(t, foreign)
	foreignHead := foreign[len(foreign)-1]
	foreignTD := foreignSeed.chain.GetTd(foreignHead.Hash(), foreignHead.NumberU64())
	if shared.NumberU64() != 24 || foreignTD.Cmp(acceptedTD) <= 0 || foreign[0].Hash() == accepted[0].Hash() {
		t.Fatal("fixture requires complete shared height 24 and an incompatible strictly heavier branch within twelve successors")
	}
	extra := &denseMinerPair{genesis: pair.genesis, miners: [2]*fixture{
		{key: acceptedSeed.key, owner: acceptedSeed.owner},
		{key: acceptedSeed.key, owner: acceptedSeed.owner},
	}}
	openDenseMinerDatabases(t, extra)
	for _, receiver := range extra.miners {
		for number := uint64(1); number <= shared.NumberU64(); number++ {
			receiver.importBlock(t, acceptedSeed.chain.GetBlockByNumber(number))
		}
	}
	for _, block := range accepted {
		extra.miners[1].importBlock(t, block)
	}
	for _, receiver := range []*fixture{acceptedSeed, extra.miners[0], extra.miners[1]} {
		for _, block := range foreign {
			if rawdb.HasHeader(receiver.db, block.Hash(), block.NumberU64()) || rawdb.HasBody(receiver.db, block.Hash(), block.NumberU64()) {
				t.Fatal("foreign ancestry was already stored in a receiver")
			}
		}
	}
	closeAutomaticSyncSeed(t, pair, 0, accepted[0])
	closeAutomaticSyncSeed(t, pair, 1, nil)
	closeAutomaticSyncSeed(t, extra, 0, accepted[0])
	closeAutomaticSyncSeed(t, extra, 1, nil)
	t.Logf("shared=%d anchor=%s acceptedHead=%s acceptedTD=%s foreignBlocks=%d foreignAnchor=%s foreignHead=%s foreignTD=%s; no foreign headers/bodies stored in any receiver", shared.NumberU64(), accepted[0].Hash(), acceptedHead.Hash(), acceptedTD, len(foreign), foreign[0].Hash(), foreignHead.Hash(), foreignTD)
	for _, scenario := range []struct {
		name       string
		localPath  string
		remotePath string
		initial    *types.Block
		want       *types.Block
		canonical  types.Blocks
		displaced  types.Blocks
		reject     bool
	}{
		{"compatible_catchup", extra.paths[0], pair.paths[0], shared, acceptedHead, accepted, nil, false},
		{"anchored_refusal", pair.paths[0], pair.paths[1], acceptedHead, acceptedHead, accepted, foreign, true},
		{"unanchored_control", extra.paths[1], pair.paths[1], acceptedHead, foreignHead, foreign, accepted, false},
	} {
		t.Run(scenario.name, func(t *testing.T) {
			local := startRehearsalNode(t, scenario.localPath)
			remote := startRehearsalNode(t, scenario.remotePath)
			before, offered := local.status(t), remote.status(t)
			requireRehearsalHead(t, before, scenario.initial)
			if (*big.Int)(offered.TD).Cmp((*big.Int)(before.TD)) <= 0 {
				t.Fatal("peer must advertise strictly greater cumulative difficulty")
			}
			requireAutomaticSyncStopped(t, before)
			requireAutomaticSyncStopped(t, offered)
			started := time.Now()
			connectRehearsalPeer(t, local, remote)
			awaitRehearsal(t, 90*time.Second-time.Since(started), func() bool {
				current := local.status(t)
				requireAutomaticSyncStopped(t, current)
				requireAutomaticSyncStopped(t, remote.status(t))
				if scenario.reject {
					requireRehearsalHead(t, current, scenario.want)
					return automaticSyncRejected(t, local.path, accepted[0], foreign[0])
				}
				return current.Hash == scenario.want.Hash() && current.Full == current.Hash && current.Header == current.Hash && current.Fast == current.Hash
			})
			t.Logf("automatic sync result=%s elapsed=%s offeredTD=%s initialTD=%s", scenario.name, time.Since(started), (*big.Int)(offered.TD), (*big.Int)(before.TD))
			requireRehearsalHead(t, local.status(t), scenario.want)
			requireAutomaticSyncLookups(t, local, scenario.canonical, scenario.displaced)
			remote.stop(t, false)
			local.stop(t, false)
			cold := startRehearsalNode(t, scenario.localPath)
			requireRehearsalHead(t, cold.status(t), scenario.want)
			requireAutomaticSyncStopped(t, cold.status(t))
			requireAutomaticSyncLookups(t, cold, scenario.canonical, scenario.displaced)
			cold.stop(t, false)
			t.Logf("live/cold canonical transactions, receipts, three heads, state and ticket commitments agree at %d %s root=%s tickets=%s", scenario.want.NumberU64(), scenario.want.Hash(), scenario.want.Root(), scenario.want.MixDigest())
		})
	}
}

func closeAutomaticSyncSeed(t *testing.T, pair *denseMinerPair, index int, anchor *types.Block) {
	t.Helper()
	closeTwoMinerSeed(t, pair.paths[index], pair.miners[index], anchor, 1)
	path := filepath.Join(pair.paths[index], "lab.json")
	var config nodeRehearsalConfig
	readHandoverJSON(t, path, &config)
	config.DenseGenesis = pair.genesis
	data, err := json.MarshalIndent(config, "", "  ")
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(path, data, 0600))
}

func requireAutomaticSyncStopped(t *testing.T, status nodeRehearsalStatus) {
	t.Helper()
	if status.Mining || status.AutoBuy || status.Signatures != 0 {
		t.Fatal("transport assertion requires mining and automatic buying stopped")
	}
}

func automaticSyncRejected(t *testing.T, path string, accepted, foreign *types.Block) bool {
	t.Helper()
	files, err := filepath.Glob(filepath.Join(path, "process-*.log"))
	requireNoError(t, err)
	for _, file := range files {
		data, err := os.ReadFile(file)
		requireNoError(t, err)
		for _, line := range strings.Split(string(data), "\n") {
			if strings.Contains(line, "Synchronisation failed") && strings.Contains(line, "restart anchor: hash mismatch") && strings.Contains(line, accepted.Hash().Hex()) && strings.Contains(line, foreign.Hash().Hex()) {
				t.Logf("observed automatic downloader rejection: %s", line)
				return true
			}
		}
	}
	return false
}

func requireAutomaticSyncLookups(t *testing.T, node *rehearsalNode, canonical, displaced types.Blocks) {
	t.Helper()
	for _, block := range canonical {
		var header *types.Header
		requireNoError(t, node.call(t, &header, "eth_getBlockByNumber", "0x"+block.Number().Text(16), false))
		if header == nil || header.Hash() != block.Hash() {
			t.Fatalf("canonical header differs at %d", block.NumberU64())
		}
		for index, tx := range block.Transactions() {
			var found *ethapi.RPCTransaction
			requireNoError(t, node.call(t, &found, "eth_getTransactionByHash", tx.Hash()))
			if found == nil || found.Hash != tx.Hash() || found.BlockHash == nil || *found.BlockHash != block.Hash() || found.BlockNumber == nil || (*big.Int)(found.BlockNumber).Cmp(block.Number()) != 0 || found.TransactionIndex == nil || uint64(*found.TransactionIndex) != uint64(index) {
				t.Fatalf("canonical transaction lookup differs for %s", tx.Hash())
			}
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if receipt == nil || receipt.TxHash != tx.Hash() || receipt.BlockHash != block.Hash() || receipt.BlockNumber == nil || receipt.BlockNumber.Cmp(block.Number()) != 0 || receipt.TransactionIndex != uint(index) || receipt.Status != types.ReceiptStatusSuccessful {
				t.Fatalf("canonical receipt differs for %s", tx.Hash())
			}
		}
	}
	for _, block := range displaced {
		for _, tx := range block.Transactions() {
			var found *ethapi.RPCTransaction
			requireNoError(t, node.call(t, &found, "eth_getTransactionByHash", tx.Hash()))
			if found != nil && found.BlockHash != nil {
				t.Fatalf("displaced transaction %s retained a canonical lookup", tx.Hash())
			}
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if receipt != nil {
				t.Fatalf("displaced transaction %s retained a receipt", tx.Hash())
			}
		}
	}
}
