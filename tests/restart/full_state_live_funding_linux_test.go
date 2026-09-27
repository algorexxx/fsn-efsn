package restart

import (
	"bytes"
	"math/big"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
)

func fundUninterruptedFullStateGap(t *testing.T, root string, nodes [2]*rehearsalNode, owners [2]common.Address, gap livePurchaseGap, first *types.Transaction) map[common.Hash]uint64 {
	t.Helper()
	requireContinuousMiners(t, nodes[0], nodes[1])
	validateLiveRepairPurchase(t, nodes[gap.index], first)
	raw, err := first.MarshalBinary()
	requireNoError(t, err)
	var hash common.Hash
	requireErrorContains(t, nodes[gap.index].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw)), "insufficient balance")
	winner := 1 - gap.index
	donor := awaitFullStateFundingDonor(t, nodes, winner)
	backup := common.HexToAddress("0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf")
	head := nodes[winner].status(t)
	funds := readPartitionFunds(t, nodes[winner], append([]common.Address{backup}, owners[:]...), head.Number)
	if funds.Block.Hash() != head.Hash || readRecoveryNodeBlock(t, nodes[gap.index], head.Number).Hash() != head.Hash {
		t.Fatal("funding inventory changed canonical branches")
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "before-funding.json"), map[string]interface{}{"Header": funds.Block.Header(), "Accounts": funds.Accounts, "Tickets": funds.Tickets, "Donor": donor, "Recipient": owners[gap.index]}))
	var transfers types.Transactions
	for i, owner := range []common.Address{backup, owners[winner]} {
		keyBytes := make([]byte, 32)
		keyBytes[31] = []byte{1, byte(winner + 2)}[i]
		key, err := crypto.ToECDSA(keyBytes)
		requireNoError(t, err)
		if crypto.PubkeyToAddress(key.PublicKey) != owner {
			t.Fatal("funding signer differs from the public synthetic fixture")
		}
		var nonce hexutil.Uint64
		requireNoError(t, nodes[winner].call(t, &nonce, "eth_getTransactionCount", owner, "pending"))
		if (i == 0 && nonce != 233429) || (i == 1 && uint64(nonce) != donor.Nonce+1) {
			t.Fatal("funding nonce changed before signing")
		}
		value := decimal(t, []string{"1200000000000000000000", "1800000000000000000000"}[i])
		if funds.Accounts[owner].BalancesVal[0].Cmp(new(big.Int).Add(value, big.NewInt(42000000000000))) < 0 {
			t.Fatal("specified funding transfer lacks existing liquid balance and gas")
		}
		transfer, err := types.SignTx(types.NewTransaction(uint64(nonce), owners[gap.index], value, 21000, big.NewInt(2000000000), nil), types.LatestSignerForChainID(first.ChainId()), key)
		requireNoError(t, err)
		transfers = append(transfers, transfer)
	}
	requireNoError(t, writeStateExportJSON(filepath.Join(root, "funding-plan.json"), map[string]interface{}{"Source": funds.Block.Header(), "Transfers": transfers, "Donor": donor, "Recipient": owners[gap.index], "Restarted": false}))
	current := readPeerPurchase(t, nodes[winner])
	if current.Nonce != donor.Nonce || !bytes.Equal(current.Saved, donor.Saved) {
		t.Fatal("donor advanced before funding submission; preserve the signed plan without replacing a nonce")
	}
	for _, transfer := range transfers {
		raw, err := transfer.MarshalBinary()
		requireNoError(t, err)
		requireNoError(t, nodes[winner].call(t, &hash, "eth_sendRawTransaction", hexutil.Bytes(raw)))
		if hash != transfer.Hash() {
			t.Fatal("funding submission changed signed identity")
		}
	}
	funding := make(map[common.Hash]uint64)
	for _, transfer := range transfers {
		receipt := awaitLiveFundingTransfer(t, nodes, transfer)
		funding[transfer.Hash()] = receipt.BlockNumber.Uint64()
	}
	t.Log("both funding transfers reached canonical success while miners and buyers remained enabled; no service restart")
	return funding
}

func awaitFullStateFundingDonor(t *testing.T, nodes [2]*rehearsalNode, index int) peerPurchaseState {
	t.Helper()
	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		requireContinuousMiners(t, nodes[0], nodes[1])
		state := readPeerPurchase(t, nodes[index])
		if len(state.Saved) > 0 && len(state.Pending) == 1 && len(state.Queued) == 0 {
			var saved types.Transaction
			requireNoError(t, saved.UnmarshalBinary(state.Saved))
			if saved.IsBuyTicketTx() && saved.Nonce() == state.Nonce && state.Pending[0].Hash() == saved.Hash() {
				return state
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	t.Fatal("no donor pending purchase available to sequence the funding transfer")
	return peerPurchaseState{}
}

func TestFullStateUninterruptedPartitionColdAudit(t *testing.T) {
	root := requireRetainedPartitionRoot(t)
	var plan struct{ Transfers types.Transactions }
	path := filepath.Join(root, "funding-plan.json")
	if _, err := os.Stat(path); err == nil {
		readHandoverJSON(t, path, &plan)
		if len(plan.Transfers) != 2 {
			t.Fatal("two specified synthetic funding transfers required")
		}
	} else if !os.IsNotExist(err) {
		t.Fatal(err)
	}
	auditRetainedPartitionCold(t, root, plan.Transfers)
}
