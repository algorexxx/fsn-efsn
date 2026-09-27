package ethapi

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/common/hexutil"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/FusionFoundation/efsn/v5/rpc"
)

const autoBuyRetryInterval = 5 * time.Second

var ticketPurchaseLock AddrLocker

type TicketBuyer struct {
	enabled bool
	cancel  context.CancelFunc
	done    chan struct{}
}

func NewTicketBuyer(enabled bool) *TicketBuyer {
	return &TicketBuyer{enabled: enabled}
}

func (buyer *TicketBuyer) Start() error {
	ctx, cancel := context.WithCancel(context.Background())
	buyer.cancel, buyer.done = cancel, make(chan struct{})
	go func() {
		defer close(buyer.done)
		AutoBuyTicket(ctx, buyer.enabled)
	}()
	return nil
}

func (buyer *TicketBuyer) Stop() error {
	buyer.cancel()
	<-buyer.done
	return nil
}

func AutoBuyTicket(ctx context.Context, enable bool) {
	ticker := time.NewTicker(autoBuyRetryInterval)
	defer ticker.Stop()
	runAutoBuyTicket(ctx, enable, time.Now, ticker.C)
}

func runAutoBuyTicket(ctx context.Context, enable bool, now func() time.Time, ticks <-chan time.Time) {
	api := fusionTransactionAPI
	common.SetAutoBuyTicketEnabled(enable)
	var lastHead common.Hash
	var lastAttempt time.Time
	var lastRebroadcast time.Time
	var lastError string
	wasEnabled := false
	for {
		enabled := common.IsAutoBuyTicketEnabled() && api.b.IsMining()
		if ctx.Err() != nil {
			return
		}
		if enabled {
			instant := now()
			head := api.b.CurrentHeader().Hash()
			if !wasEnabled || head != lastHead || instant.Sub(lastAttempt) >= autoBuyRetryInterval {
				lastHead, lastAttempt = head, instant
				attempt, cancel := context.WithTimeout(ctx, autoBuyRetryInterval)
				rebroadcast := instant.Sub(lastRebroadcast) >= autoBuyRetryInterval
				if rebroadcast {
					lastRebroadcast = instant
				}
				err := api.reconcileTicketPurchase(attempt, rebroadcast)
				cancel()
				if err != nil && err.Error() != lastError && ctx.Err() == nil {
					log.Warn("Automatic ticket purchase needs attention; retrying", "err", err)
					lastError = err.Error()
				} else if err == nil {
					lastError = ""
				}
			}
		}
		wasEnabled = enabled
		select {
		case <-ctx.Done():
			return
		case <-ticks:
		case <-common.AutoBuyTicketChan:
		}
	}
}

func (s *FusionTransactionAPI) reconcileTicketPurchase(ctx context.Context, rebroadcast bool) error {
	owner, err := s.b.Coinbase()
	if err != nil {
		return err
	}
	ticketPurchaseLock.LockAddr(owner)
	defer ticketPurchaseLock.UnlockAddr(owner)
	s.nonceLock.LockAddr(owner)
	defer s.nonceLock.UnlockAddr(owner)
	statedb, header, err := s.b.StateAndHeaderByNumber(ctx, rpc.LatestBlockNumber)
	if err != nil {
		return err
	}
	if statedb == nil || header == nil {
		return fmt.Errorf("latest state is unavailable")
	}
	nonce := statedb.GetNonce(owner)
	if err := statedb.Error(); err != nil {
		return err
	}
	tx, err := s.loadAutomaticTicket(owner)
	if err != nil {
		return err
	}
	if tx != nil && tx.Nonce() < nonce {
		if err := s.finishAutomaticTicket(ctx, owner, tx, header.Hash()); err != nil {
			return err
		}
		tx = nil
	}
	pending, queued := s.b.TxPoolContent()
	pool := append(pending[owner], queued[owner]...)
	for _, candidate := range pool {
		if candidate.Nonce() < nonce {
			continue
		}
		if tx != nil && candidate.Nonce() == tx.Nonce() && candidate.Hash() != tx.Hash() {
			return fmt.Errorf("automatic ticket %s was replaced at nonce %d by %s; awaiting nonce resolution", tx.Hash(), tx.Nonce(), candidate.Hash())
		}
		if tx != nil && candidate.Hash() != tx.Hash() && isTicketPurchase(candidate) {
			return fmt.Errorf("another ticket purchase %s is pending; awaiting nonce resolution", candidate.Hash())
		}
		if tx == nil && isTicketPurchase(candidate) {
			tx = candidate
			if err := s.saveAutomaticTicket(owner, tx); err != nil {
				return err
			}
		}
	}
	if tx != nil {
		if tx.Nonce() != nonce {
			return fmt.Errorf("automatic ticket %s needs nonce %d, current nonce is %d", tx.Hash(), tx.Nonce(), nonce)
		}
		for _, candidate := range pending[owner] {
			if candidate.Hash() == tx.Hash() {
				if !rebroadcast {
					return nil
				}
				if err := ctx.Err(); err != nil {
					return err
				}
				if !common.IsAutoBuyTicketEnabled() || !s.b.IsMining() {
					return nil
				}
				if s.b.CurrentHeader().Hash() != header.Hash() {
					return fmt.Errorf("head changed while checking pending ticket purchase")
				}
				return s.b.RebroadcastTx(ctx, tx)
			}
		}
		for _, candidate := range queued[owner] {
			if candidate.Hash() == tx.Hash() {
				return nil
			}
		}
		return s.submitAutomaticTicket(ctx, tx)
	}
	for _, candidate := range pool {
		if candidate.Nonce() >= nonce {
			return fmt.Errorf("account has another pending transaction %s; awaiting nonce resolution", candidate.Hash())
		}
	}
	args := common.BuyTicketArgs{FusionBaseArgs: common.FusionBaseArgs{From: owner, Nonce: (*hexutil.Uint64)(&nonce)}}
	unsigned, err := s.BuildBuyTicketTx(ctx, args)
	if err != nil {
		return err
	}
	tx, err = s.signTransaction(owner, unsigned)
	if err != nil {
		return err
	}
	if s.b.CurrentHeader().Hash() != header.Hash() {
		return fmt.Errorf("head changed while constructing ticket purchase; retrying against new state")
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if !common.IsAutoBuyTicketEnabled() || !s.b.IsMining() {
		return nil
	}
	if err := s.saveAutomaticTicket(owner, tx); err != nil {
		return err
	}
	return s.submitAutomaticTicket(ctx, tx)
}

func automaticTicketKey(owner common.Address) []byte {
	return append([]byte("fsn-auto-ticket-v1-"), owner[:]...)
}

func (s *FusionTransactionAPI) loadAutomaticTicket(owner common.Address) (*types.Transaction, error) {
	key := automaticTicketKey(owner)
	exists, err := s.b.ChainDb().Has(key)
	if err != nil || !exists {
		return nil, err
	}
	data, err := s.b.ChainDb().Get(key)
	if err != nil {
		return nil, err
	}
	var tx types.Transaction
	if err := tx.UnmarshalBinary(data); err != nil {
		return nil, fmt.Errorf("invalid saved automatic ticket: %w", err)
	}
	sender, err := types.Sender(types.LatestSigner(s.b.ChainConfig()), &tx)
	if err != nil || sender != owner || !isTicketPurchase(&tx) {
		return nil, fmt.Errorf("saved automatic ticket has an invalid sender or payload")
	}
	return &tx, nil
}

func (s *FusionTransactionAPI) saveAutomaticTicket(owner common.Address, tx *types.Transaction) error {
	data, err := tx.MarshalBinary()
	if err != nil {
		return err
	}
	return s.b.ChainDb().Put(automaticTicketKey(owner), data)
}

func (s *FusionTransactionAPI) submitAutomaticTicket(ctx context.Context, tx *types.Transaction) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if !common.IsAutoBuyTicketEnabled() || !s.b.IsMining() {
		return nil
	}
	if _, err := s.SendRawTransaction(ctx, tx); err != nil {
		return err
	}
	log.Info("Automatic ticket submitted; awaiting inclusion", "tx", tx.Hash(), "nonce", tx.Nonce())
	return nil
}

func (s *FusionTransactionAPI) finishAutomaticTicket(ctx context.Context, owner common.Address, tx *types.Transaction, head common.Hash) error {
	included, hash, number, index, err := s.b.GetTransaction(ctx, tx.Hash())
	if err != nil {
		return err
	}
	confirmed := false
	if included != nil {
		header, err := s.b.HeaderByNumber(ctx, rpc.BlockNumber(number))
		if err != nil {
			return err
		}
		if header == nil || header.Hash() != hash {
			return fmt.Errorf("ticket inclusion changed during reconciliation")
		}
		receipts, err := s.b.GetReceipts(ctx, hash)
		if err != nil {
			return err
		}
		if index >= uint64(len(receipts)) || receipts[index] == nil || receipts[index].TxHash != tx.Hash() {
			return fmt.Errorf("ticket receipt unavailable")
		}
		expected := crypto.Keccak256Hash(owner[:], header.ParentHash[:])
		for _, entry := range receipts[index].Logs {
			if entry.Address != common.FSNCallAddress || len(entry.Topics) == 0 || entry.Topics[0] != common.BytesToHash([]byte{byte(common.BuyTicketFunc)}) {
				continue
			}
			var outcome struct {
				TicketID    common.Hash
				TicketOwner common.Address
				Error       string
			}
			if json.Unmarshal(entry.Data, &outcome) == nil && outcome.Error == "" && outcome.TicketID == expected && outcome.TicketOwner == owner && receipts[index].Status == types.ReceiptStatusSuccessful {
				confirmed = true
			}
		}
	}
	if s.b.CurrentHeader().Hash() != head {
		return fmt.Errorf("head changed while checking ticket inclusion")
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := s.b.ChainDb().Delete(automaticTicketKey(owner)); err != nil {
		return err
	}
	if confirmed {
		log.Info("Automatic ticket purchase confirmed", "tx", tx.Hash(), "block", hash)
	} else {
		log.Warn("Automatic ticket nonce consumed without a confirmed purchase", "tx", tx.Hash(), "nonce", tx.Nonce())
	}
	return nil
}

func isTicketPurchase(tx *types.Transaction) bool {
	if tx.To() == nil || *tx.To() != common.FSNCallAddress {
		return false
	}
	var envelope common.FSNCallParam
	var purchase common.BuyTicketParam
	return rlp.DecodeBytes(tx.Data(), &envelope) == nil && envelope.Func == common.BuyTicketFunc && rlp.DecodeBytes(envelope.Data, &purchase) == nil
}

func checkPendingTicketPurchase(b Backend, args common.BuyTicketArgs) error {
	pending := b.GetPoolTransactionByPredicate(func(tx *types.Transaction) bool {
		if !isTicketPurchase(tx) {
			return false
		}
		owner, err := types.Sender(types.LatestSigner(b.ChainConfig()), tx)
		return err == nil && owner == args.From
	})
	if pending != nil && (args.Nonce == nil || uint64(*args.Nonce) != pending.Nonce()) {
		return fmt.Errorf("ticket purchase already pending: %s", pending.Hash())
	}
	return nil
}
