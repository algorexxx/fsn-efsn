package discover

import (
	"context"
	"net"
	"testing"
	"time"
)

func TestRestartBootstrapRefreshKeepsResolvedAddress(t *testing.T) {
	table, err := newTable(newPingRecorder(), NodeID{}, &net.UDPAddr{}, "", nil)
	if err != nil {
		t.Fatal(err)
	}
	defer table.db.close()
	old := restartCacheNode(t, 1)
	old.IP = net.IP{127, 0, 0, 1}
	if err := table.db.updateNode(old); err != nil {
		t.Fatal(err)
	}
	if err := table.db.updateLastPongReceived(old.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	seed := restartCacheNode(t, 1)
	seed.IP = nil
	seed.hostname = "127.0.0.2"
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	done := make(chan struct{})
	go func() {
		select {
		case request := <-table.refreshReq:
			table.loadSeedNodes()
			close(request)
		case <-ctx.Done():
		}
		close(done)
	}()
	if err := table.resolveBootstrap(ctx, seed); err != nil {
		t.Fatal(err)
	}
	<-done
	table.mutex.Lock()
	defer table.mutex.Unlock()
	peers := table.closest(seed.sha, bucketSize).entries
	if len(peers) != 1 || !peers[0].IP.Equal(net.IP{127, 0, 0, 2}) {
		t.Fatalf("refresh replaced newly resolved endpoint with old database entry: %v", peers)
	}
}
