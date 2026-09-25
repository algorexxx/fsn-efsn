package discover

import (
	"fmt"
	"net"
	"path/filepath"
	"reflect"
	"sort"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/crypto"
)

func TestRestartPeerCacheMaturation(t *testing.T) {
	path := filepath.Join(t.TempDir(), "nodes")
	table, err := newTable(newPingRecorder(), NodeID{}, &net.UDPAddr{}, path, nil)
	if err != nil {
		t.Fatal(err)
	}
	young := restartCacheNode(t, 1)
	mature := restartCacheNode(t, 2)
	table.add(young)
	table.add(mature)
	young.addedAt = time.Now().Add(-4 * time.Minute)
	mature.addedAt = time.Now().Add(-6 * time.Minute)
	table.copyLiveNodes()
	table.db.close()
	database, err := newNodeDB(path, nodeDBVersion, NodeID{})
	if err != nil {
		t.Fatal(err)
	}
	defer database.close()
	if database.node(young.ID) != nil {
		t.Fatal("four-minute peer was persisted")
	}
	saved := database.node(mature.ID)
	if saved == nil || saved.String() != mature.String() {
		t.Fatal("six-minute peer did not survive closed database reopen")
	}
	t.Log("four-minute contact excluded; six-minute contact persisted and survived reopen")
}

func TestRestartPeerRefreshPreservesMaturation(t *testing.T) {
	table, err := newTable(newPingRecorder(), NodeID{}, &net.UDPAddr{}, "", nil)
	if err != nil {
		t.Fatal(err)
	}
	defer table.db.close()
	original := restartCacheNode(t, 1)
	table.add(original)
	original.addedAt = time.Now().Add(-time.Minute)
	addedAt := original.addedAt
	refreshed := restartCacheNode(t, 1)
	table.add(refreshed)
	table.copyLiveNodes()
	if !refreshed.addedAt.Equal(addedAt) {
		t.Errorf("peer refresh lost original table age: original=%s refreshed=%s", addedAt.Format(time.RFC3339Nano), refreshed.addedAt.Format(time.RFC3339Nano))
	}
	if table.db.node(original.ID) != nil {
		t.Error("one-minute peer was prematurely persisted after refresh")
	}
}

func TestRestartPeerCacheAgeAndCleanup(t *testing.T) {
	path := filepath.Join(t.TempDir(), "nodes")
	database, err := newNodeDB(path, nodeDBVersion, NodeID{})
	if err != nil {
		t.Fatal(err)
	}
	ages := []time.Duration{time.Hour, 48 * time.Hour, 6 * 24 * time.Hour}
	for i, age := range ages {
		peer := restartCacheNode(t, i+1)
		if err := database.updateNode(peer); err != nil {
			t.Fatal(err)
		}
		if err := database.updateLastPongReceived(peer.ID, time.Now().Add(-age)); err != nil {
			t.Fatal(err)
		}
	}
	database.close()
	database, err = newNodeDB(path, nodeDBVersion, NodeID{})
	if err != nil {
		t.Fatal(err)
	}
	defer database.close()
	wantBefore := []string{restartCacheNode(t, 1).ID.String(), restartCacheNode(t, 2).ID.String()}
	wantAfter := []string{restartCacheNode(t, 1).ID.String()}
	sort.Strings(wantBefore)
	before := restartCacheIDs(database.querySeeds(30, seedMaxAge))
	if err := database.expireNodes(); err != nil {
		t.Fatal(err)
	}
	after := restartCacheIDs(database.querySeeds(30, seedMaxAge))
	if !reflect.DeepEqual(before, wantBefore) || !reflect.DeepEqual(after, wantAfter) {
		t.Fatalf("cache eligibility mismatch: before=%v after=%v", before, after)
	}
	t.Log("cold seed query admits one-hour and two-day contacts, excludes six-day contact; explicit cleanup keeps only the one-hour contact")
}

func restartCacheNode(t *testing.T, number int) *Node {
	t.Helper()
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", number))
	if err != nil {
		t.Fatal(err)
	}
	return NewNode(PubkeyID(&key.PublicKey), net.IPv4(127, 0, 0, byte(number+1)), 40408, 40408)
}

func restartCacheIDs(peers []*Node) []string {
	ids := make([]string, 0, len(peers))
	for _, peer := range peers {
		ids = append(ids, peer.ID.String())
	}
	sort.Strings(ids)
	return ids
}
