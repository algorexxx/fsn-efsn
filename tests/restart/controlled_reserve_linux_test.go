package restart

import (
	"math/big"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/consensus/datong"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func rehearseControlledZeroTicketReserves(t *testing.T) {
	prefix := buildControlledReservePrefix(t)
	for _, scenario := range []struct {
		name       string
		funding    string
		sponsorEnd string
		missAgain  bool
	}{
		{"no_funding", "0", "11000000000000000000000", false},
		{"one_ticket_funding", "5000000000000000000000", "5999999979000000000000", false},
		{"two_ticket_funding", "10000000000000000000000", "999999979000000000000", false},
		{"one_ticket_missed_again", "5000000000000000000000", "5999999979000000000000", true},
	} {
		t.Run(scenario.name, func(t *testing.T) {
			pair := replayControlledReservePrefix(t, prefix)
			affected, healthy := pair.miners[prefix.affected], pair.miners[1-prefix.affected]
			requireErrorContains(t, controlledPurchaseAdmission(affected, prefix.originals[0]), "insufficient balance")
			var transfer *types.Transaction
			var included types.Transactions
			waited := 0
			if scenario.funding == "0" {
				for i := 0; i < 12; i++ {
					appendControlledReserveBlock(t, pair, 1-prefix.affected, 1-prefix.affected, nil)
					requireErrorContains(t, controlledPurchaseAdmission(affected, prefix.originals[0]), "insufficient balance")
				}
				t.Log("controlled no-funding: twelve canonical blocks advanced; zero tickets and no repair admitted")
			} else {
				var err error
				transfer, err = types.SignTx(types.NewTransaction(0, affected.owner, decimal(t, scenario.funding), 21000, big.NewInt(1000000000), nil), types.LatestSigner(affected.chain.Config()), prefix.funder.key)
				requireNoError(t, err)
				appendControlledReserveBlock(t, pair, 1-prefix.affected, 1-prefix.affected, types.Transactions{transfer})
				for _, tx := range prefix.originals {
					waited += awaitControlledPurchaseFunds(t, pair, prefix, tx)
					producer := preferredFixtureProducer(t, affected, healthy)
					index := prefix.affected
					if producer == healthy {
						index = 1 - prefix.affected
					}
					block := appendControlledReserveBlock(t, pair, index, 1-prefix.affected, types.Transactions{tx})
					requireNoControlledRetreat(t, block)
					included = append(included, tx)
					t.Logf("controlled original nonce=%d hash=%s included=%d block=%s", tx.Nonce(), tx.Hash().Hex(), block.NumberU64(), block.Hash().Hex())
					if scenario.missAgain {
						retreatControlledReplacement(t, pair, prefix, prefix.originals[1])
						break
					}
				}
			}
			state, err := affected.chain.State()
			requireNoError(t, err)
			if state.GetNonce(affected.owner) != prefix.originals[0].Nonce()+uint64(len(included)) {
				t.Fatal("controlled canonical nonce differs from exact included purchases")
			}
			head := affected.chain.CurrentBlock()
			t.Logf("controlled result case=%s baseline=%s topup-wei=%s included=%d funding-wait-blocks=%d final=%d hash=%s state=%s tickets=%s", scenario.name, prefix.blocks[len(prefix.blocks)-1].Hash().Hex(), scenario.funding, len(included), waited, head.NumberU64(), head.Hash().Hex(), head.Root().Hex(), head.MixDigest().Hex())
			verifyControlledReserveCold(t, pair, prefix, transfer, included, scenario.sponsorEnd)
		})
	}
}

func controlledPurchaseAdmission(owner *fixture, tx *types.Transaction) error {
	config := core.DefaultTxPoolConfig
	config.Journal = ""
	pool := core.NewTxPool(config, owner.chain.Config(), owner.chain)
	defer pool.Stop()
	return pool.AddLocal(tx)
}

func awaitControlledPurchaseFunds(t *testing.T, pair *denseMinerPair, prefix *controlledReservePrefix, tx *types.Transaction) int {
	t.Helper()
	affected, healthy := pair.miners[prefix.affected], pair.miners[1-prefix.affected]
	for waited := 0; waited <= 32; waited++ {
		err := controlledPurchaseAdmission(affected, tx)
		if err == nil {
			t.Logf("controlled admission nonce=%d hash=%s waited-blocks=%d", tx.Nonce(), tx.Hash().Hex(), waited)
			return waited
		}
		requireErrorContains(t, err, "insufficient balance")
		if waited == 32 {
			break
		}
		producer := preferredFixtureProducer(t, affected, healthy)
		index := prefix.affected
		if producer == healthy {
			index = 1 - prefix.affected
		}
		block := appendControlledReserveBlock(t, pair, index, 1-prefix.affected, nil)
		requireNoControlledRetreat(t, block)
	}
	t.Fatal("controlled purchase remained unfunded after 32 first-ranked producer blocks")
	return 0
}

func requireNoControlledRetreat(t *testing.T, block *types.Block) {
	t.Helper()
	snapshot, err := datong.NewSnapshotFromHeader(block.Header())
	requireNoError(t, err)
	if len(snapshot.Retreat) != 0 {
		t.Fatal("cooperative controlled recovery introduced an additional first-retreat loss")
	}
}

func retreatControlledReplacement(t *testing.T, pair *denseMinerPair, prefix *controlledReservePrefix, next *types.Transaction) {
	t.Helper()
	affected := pair.miners[prefix.affected]
	for i := 0; i < 32; i++ {
		block := appendControlledReserveBlock(t, pair, 1-prefix.affected, 1-prefix.affected, nil)
		snapshot, err := datong.NewSnapshotFromHeader(block.Header())
		requireNoError(t, err)
		if len(snapshot.Retreat) == 0 {
			continue
		}
		state, err := affected.chain.State()
		requireNoError(t, err)
		tickets, err := state.AllTickets()
		requireNoError(t, err)
		if len(snapshot.Retreat) != 1 || tickets.NumberOfTicketsByAddress(affected.owner) != 0 {
			t.Fatal("missed replacement did not cause exactly one further loss and zero tickets")
		}
		requireErrorContains(t, controlledPurchaseAdmission(affected, next), "insufficient balance")
		t.Logf("controlled missed-again: replacement retreated at block=%d hash=%s ticket=%s; next nonce=%d remains unfunded", block.NumberU64(), block.Hash().Hex(), snapshot.Retreat[0].Hex(), next.Nonce())
		return
	}
	t.Fatal("controlled missed replacement was not retreated within 32 blocks")
}

func verifyControlledReserveCold(t *testing.T, pair *denseMinerPair, prefix *controlledReservePrefix, transfer *types.Transaction, included types.Transactions, sponsorEnd string) {
	t.Helper()
	head := pair.miners[0].chain.CurrentBlock()
	owner := pair.miners[prefix.affected].owner
	owners := []common.Address{pair.miners[0].owner, pair.miners[1].owner, prefix.funder.owner}
	closeDenseMinerPair(t, pair)
	for i, path := range pair.paths {
		node := startRehearsalNode(t, path)
		requireRehearsalHead(t, node.status(t), head)
		var nonce hexutil.Uint64
		requireNoError(t, node.call(t, &nonce, "eth_getTransactionCount", owner, "latest"))
		if uint64(nonce) != prefix.originals[0].Nonce()+uint64(len(included)) {
			t.Fatal("cold controlled nonce differs")
		}
		for _, tx := range included {
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", tx.Hash()))
			if receipt == nil {
				t.Fatal("cold controlled purchase receipt missing")
			}
			requirePeerNativePurchase(t, receipt, readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64()), tx, owner)
		}
		var balance string
		requireNoError(t, node.call(t, &balance, "fsn_getBalance", common.SystemAssetID, prefix.funder.owner, "latest"))
		requireNoError(t, node.call(t, &nonce, "eth_getTransactionCount", prefix.funder.owner, "latest"))
		if balance != sponsorEnd || (transfer == nil && nonce != 0) || (transfer != nil && nonce != 1) {
			t.Fatal("cold sponsor balance or nonce differs from the one-transfer funding budget")
		}
		if transfer != nil {
			var receipt *types.Receipt
			requireNoError(t, node.call(t, &receipt, "eth_getTransactionReceipt", transfer.Hash()))
			if receipt == nil || receipt.Status != types.ReceiptStatusSuccessful || receipt.GasUsed != 21000 || readRecoveryNodeBlock(t, node, receipt.BlockNumber.Uint64()).Hash() != receipt.BlockHash {
				t.Fatal("cold funding transfer was not canonical and successful")
			}
		}
		if i == 0 {
			auditPartitionFunds(t, node, owners, 24, head.NumberU64(), "controlled")
		}
		t.Logf("controlled cold node=%d purchases=%d sponsor-nonce=%d sponsor-liquid-wei=%s head=%s", i+1, len(included), nonce, balance, head.Hash().Hex())
		node.stop(t, false)
	}
}
