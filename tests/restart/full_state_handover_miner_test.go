package restart

import (
	"math/big"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/accounts"
	"github.com/FusionFoundation/efsn/v5/accounts/keystore"
	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/event"
	"github.com/FusionFoundation/efsn/v5/internal/ethapi"
	"github.com/FusionFoundation/efsn/v5/miner"
)

func runFullStateHandoverMiner(t *testing.T, directory, artifacts string) {
	t.Helper()
	f, original, funding := openFullStateHandover(t, directory)
	selectHandoverSuccessor(t, f, funding)
	initial := f.chain.CurrentBlock()
	offset := initial.NumberU64() - funding.Parent.Number.Uint64()
	if offset != 6 && offset != 8 {
		t.Fatal("worker phase must start after six constructed blocks or two prior worker blocks")
	}
	if uint64(time.Now().Unix()) >= ticketEnd {
		t.Fatal("fixed rehearsal tickets expired; choose and review a fresh test interval")
	}
	s, err := f.chain.State()
	requireNoError(t, err)
	tickets, err := s.AllTickets()
	requireNoError(t, err)
	if tickets.NumberOfTickets() != 1 || tickets.NumberOfTicketsByAddress(f.owner) != 1 {
		t.Fatal("worker phase requires only the successor's remaining ticket")
	}
	keys := keystore.NewKeyStore(t.TempDir(), keystore.LightScryptN, keystore.LightScryptP)
	account, err := keys.ImportECDSA(f.key, "public-synthetic-key")
	requireNoError(t, err)
	requireNoError(t, keys.Unlock(account, "public-synthetic-key"))
	manager := accounts.NewManager(keys)
	t.Cleanup(func() { manager.Close() })
	b := &autoBuyBackend{purchaseBackend: &purchaseBackend{chain: f.chain}, pool: f.newPool(t), accounts: manager, owner: f.owner, database: f.db, submissions: make(chan purchaseSubmission, 16), initialized: make(chan struct{}, 1)}
	f.engine.Authorize(f.owner, func(_ accounts.Account, _ string, data []byte) ([]byte, error) {
		return crypto.Sign(crypto.Keccak256(data), f.key)
	})
	mux := new(event.TypeMux)
	b.miner = miner.New(b, &miner.Config{GasCeil: initial.GasLimit(), GasPrice: big.NewInt(1), Recommit: time.Second}, f.chain.Config(), mux, f.engine, func(block *types.Block) bool { return block.Coinbase() == f.owner })
	var closeMiner sync.Once
	t.Cleanup(func() { closeMiner.Do(b.miner.Close); mux.Stop() })
	lock := new(ethapi.AddrLocker)
	ethapi.NewFusionTransactionAPI(b, lock, ethapi.NewPublicTransactionPoolAPI(b, lock))
	heads := make(chan core.ChainHeadEvent, 16)
	subscription := f.chain.SubscribeChainHeadEvent(heads)
	t.Cleanup(subscription.Unsubscribe)
	b.miner.Start(f.owner)
	awaitMining(t, b.miner)
	if offset == 6 {
		b.failNext.Store(true)
	}
	stopPurchases := startPurchaseController(t, true)
	submitted := awaitSubmission(t, b)
	if offset == 6 {
		requireErrorContains(t, submitted.err, "injected temporary submission failure")
		if f.chain.CurrentBlock().Hash() != initial.Hash() {
			t.Fatal("failed startup submission advanced the head")
		}
		retried := awaitSubmission(t, b)
		requireNoError(t, retried.err)
		if submitted.tx.Hash() != retried.tx.Hash() {
			t.Fatal("retry changed the saved transaction")
		}
		t.Logf("startup submission failure retried without a new head; identical signed transaction=%s", retried.tx.Hash().Hex())
	} else {
		requireNoError(t, submitted.err)
		t.Logf("cold worker/controller restart submitted replacement=%s nonce=%d", submitted.tx.Hash().Hex(), submitted.tx.Nonce())
	}
	first := awaitHead(t, heads)
	secondPurchase := awaitSubmission(t, b)
	requireNoError(t, secondPurchase.err)
	second := awaitHead(t, heads)
	stopPurchases()
	closeMiner.Do(b.miner.Close)
	if f.chain.CurrentBlock().Hash() != second.Hash() {
		t.Fatal("worker advanced past the bounded two-block phase")
	}
	for i, block := range []*types.Block{first, second} {
		if block.NumberU64() != initial.NumberU64()+uint64(i)+1 || block.Coinbase() != funding.Successor || len(block.Transactions()) != 1 {
			t.Fatal("unexpected worker-produced handover block")
		}
		expected := submitted.tx.Hash()
		if i == 1 {
			expected = secondPurchase.tx.Hash()
		}
		if block.Transactions()[0].Hash() != expected {
			t.Fatal("worker included another transaction")
		}
		recordFullStateHandoverBlock(t, f, artifacts, funding.Parent.Number.Uint64(), block)
	}
	s, err = f.chain.State()
	requireNoError(t, err)
	if s.GetNonce(original.SyntheticOwner) != original.Nonce || s.GetNonce(funding.Successor) != funding.Nonce+offset+2 || common.IsAutoBuyTicketEnabled() {
		t.Fatal("unexpected nonce or automatic purchases still enabled")
	}
	t.Logf("real worker and automatic buyer completed two blocks; offset=%d..%d originalNonce=%d successorNonce=%d", offset+1, offset+2, s.GetNonce(original.SyntheticOwner), s.GetNonce(funding.Successor))
}
