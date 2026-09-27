package eth

import (
	"bytes"
	"context"
	"math/big"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
)

func TestAutomaticTicketRebroadcastQueues(t *testing.T) {
	tx := types.NewTransaction(9, common.FSNCallAddress, new(big.Int), 21224, big.NewInt(1000000001), []byte{1, 2, 3})
	for _, mode := range []string{"known", "full-queue", "cancelled", "closed"} {
		t.Run(mode, func(t *testing.T) {
			pm := &ProtocolManager{peers: newPeerSet()}
			for _, id := range []byte{1, 2} {
				p := newPeer(eth63, p2p.NewPeer(discover.NodeID{id}, "test", nil), nil)
				p.MarkTransaction(tx.Hash())
				pm.peers.peers[p.id] = p
			}
			var full *peer
			if mode == "full-queue" {
				for _, p := range pm.peers.peers {
					full = p
					break
				}
				for len(full.queuedTxs) < cap(full.queuedTxs) {
					full.queuedTxs <- types.Transactions{tx}
				}
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if mode == "cancelled" {
				cancel()
			}
			pm.peers.closed = mode == "closed"
			done := make(chan error, 1)

			go func() { done <- pm.rebroadcastTx(ctx, tx) }()

			select {
			case err := <-done:
				if err != ctx.Err() {
					t.Fatalf("error=%v", err)
				}
			case <-time.After(time.Second):
				t.Fatal("rebroadcast blocked on a full peer queue")
			}
			for _, p := range pm.peers.peers {
				want := 1
				if mode == "cancelled" || mode == "closed" {
					want = 0
				}
				if p == full {
					want = cap(p.queuedTxs)
				}
				if len(p.queuedTxs) != want {
					t.Fatalf("queued=%d want=%d", len(p.queuedTxs), want)
				}
				if !p.knownTxs.Contains(tx.Hash()) {
					t.Fatal("known tracking was cleared")
				}
			}
		})
	}
}

func TestAutomaticTicketRebroadcastWire(t *testing.T) {
	left, right := p2p.MsgPipe()
	defer left.Close()
	pm := &ProtocolManager{peers: newPeerSet()}
	p := newPeer(eth63, p2p.NewPeer(discover.NodeID{1}, "receiver", nil), left)
	if err := pm.peers.Register(p); err != nil {
		t.Fatal(err)
	}
	defer pm.peers.Unregister(p.id)
	tx := types.NewTransaction(9, common.FSNCallAddress, new(big.Int), 21224, big.NewInt(1000000001), []byte{1, 2, 3})
	p.MarkTransaction(tx.Hash())
	encoded, err := tx.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}
	read := make(chan types.Transactions, 1)
	errors := make(chan error, 1)
	go func() {
		msg, err := right.ReadMsg()
		if err != nil {
			errors <- err
			return
		}
		defer msg.Discard()
		var batch types.Transactions
		if err := msg.Decode(&batch); err != nil {
			errors <- err
			return
		}
		read <- batch
	}()

	err = pm.rebroadcastTx(context.Background(), tx)

	if err != nil {
		t.Fatal(err)
	}
	select {
	case batch := <-read:
		if len(batch) != 1 {
			t.Fatal("unexpected wire batch")
		}
		actual, err := batch[0].MarshalBinary()
		if err != nil || !bytes.Equal(actual, encoded) {
			t.Fatal("wire bytes changed")
		}
	case err := <-errors:
		t.Fatal(err)
	case <-time.After(time.Second):
		t.Fatal("known peer did not receive retry")
	}
}
