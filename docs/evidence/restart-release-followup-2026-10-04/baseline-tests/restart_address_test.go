package discover

import (
	"fmt"
	"net"
	"testing"
	"time"
)

func restartAddressTable(t *testing.T, transport transport) *Table {
	t.Helper()
	tab, err := newTable(transport, NodeID{}, &net.UDPAddr{}, "", nil)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(tab.db.close)
	return tab
}

func restartAddressNode(t *testing.T, tab *Table, number, bucketIndex int, address string) *Node {
	t.Helper()
	n := restartCacheNode(t, number)
	n.IP = net.ParseIP(address)
	n.sha = hashAtDistance(tab.self.sha, bucketMinDistance+1+bucketIndex)
	return n
}

func restartMovedNode(n *Node, address string) *Node {
	moved := *n
	moved.IP = net.ParseIP(address)
	return &moved
}

func TestRestartPeerAddressMove(t *testing.T) {
	for _, test := range []struct {
		name, old, next, counts string
	}{
		{"public_subnet", "172.0.1.1", "172.0.2.1", "{172.0.2.0×1}"},
		{"same_subnet", "172.0.1.1", "172.0.1.2", "{172.0.1.0×1}"},
		{"lan_to_public", "10.0.1.1", "172.0.2.1", "{172.0.2.0×1}"},
		{"public_to_lan", "172.0.1.1", "10.0.1.1", "{}"},
		{"ipv6_subnet", "2001:4860::1", "2606:4700::1", "{2606:4700::×1}"},
		{"ipv4_to_ipv6", "172.0.1.1", "2606:4700::1", "{2606:4700::×1}"},
	} {
		t.Run(test.name, func(t *testing.T) {
			tab := restartAddressTable(t, newPingRecorder())
			original := restartAddressNode(t, tab, 1, 0, test.old)
			tab.add(original)
			age := original.addedAt
			moved := restartMovedNode(original, test.next)

			tab.add(moved)

			b := tab.bucket(original.sha)
			if len(b.entries) != 1 || b.entries[0] != moved || !moved.addedAt.Equal(age) {
				t.Error("address update lost identity or original residence time")
			}
			if tab.ips.String() != test.counts || b.ips.String() != test.counts {
				t.Fatalf("subnet reservations: table=%s bucket=%s want=%s", tab.ips.String(), b.ips.String(), test.counts)
			}
		})
	}
}

func TestRestartPeerAddressMoveLimits(t *testing.T) {
	for _, mode := range []string{"bucket_full", "table_full", "same_subnet_full"} {
		t.Run(mode, func(t *testing.T) {
			tab := restartAddressTable(t, newPingRecorder())
			original := restartAddressNode(t, tab, 1, 0, "172.0.1.1")
			tab.add(original)
			count := 2
			if mode == "table_full" {
				count = 10
			}
			if mode == "same_subnet_full" {
				count = 1
			}
			for i := 0; i < count; i++ {
				bucketIndex := 0
				address := fmt.Sprintf("172.0.2.%d", i+1)
				if mode == "table_full" {
					bucketIndex = i/2 + 1
				}
				if mode == "same_subnet_full" {
					address = "172.0.1.2"
				}
				tab.add(restartAddressNode(t, tab, i+2, bucketIndex, address))
			}
			before := tab.ips.String()
			moved := restartMovedNode(original, "172.0.2.99")
			want := original
			if mode == "same_subnet_full" {
				moved.IP = net.ParseIP("172.0.1.99")
				want = moved
			}

			tab.add(moved)

			b := tab.bucket(original.sha)
			for _, n := range b.entries {
				if n.ID == original.ID && n != want {
					t.Errorf("wrong endpoint after quota check: got=%s want=%s", n.addr(), want.addr())
				}
			}
			if len(b.replacements) != 0 || tab.ips.String() != before {
				t.Fatalf("move changed existing reservations or duplicated identity: before=%s after=%s replacements=%d", before, tab.ips.String(), len(b.replacements))
			}
		})
	}
}

func TestRestartPeerAddressMoveReleasesCapacity(t *testing.T) {
	tab := restartAddressTable(t, newPingRecorder())
	original := restartAddressNode(t, tab, 1, 0, "172.0.1.1")
	tab.add(original)
	tab.add(restartMovedNode(original, "172.0.2.1"))
	tab.add(restartAddressNode(t, tab, 2, 0, "172.0.1.2"))
	tab.add(restartAddressNode(t, tab, 3, 0, "172.0.1.3"))
	tab.add(restartAddressNode(t, tab, 4, 0, "172.0.2.2"))
	overLimit := restartAddressNode(t, tab, 5, 0, "172.0.2.3")

	tab.add(overLimit)

	b := tab.bucket(original.sha)
	if len(b.entries) != 4 || contains(b.entries, overLimit.ID) || len(b.replacements) != 0 {
		t.Fatalf("old capacity was not released or new subnet limit bypassed: entries=%d overLimit=%t replacements=%d", len(b.entries), contains(b.entries, overLimit.ID), len(b.replacements))
	}
	if tab.ips.String() != "{172.0.1.0×2 172.0.2.0×2}" {
		t.Fatalf("incorrect reservations: %s", tab.ips.String())
	}
}

func restartFullAddressBucket(t *testing.T, tab *Table) *bucket {
	t.Helper()
	for i := 0; i < bucketSize; i++ {
		tab.add(restartAddressNode(t, tab, i+1, 0, fmt.Sprintf("172.1.%d.1", i)))
	}
	return tab.buckets[0]
}

func TestRestartPeerReplacementAddress(t *testing.T) {
	for _, mode := range []string{"move", "reject_full_subnet", "promote_same", "promote_moved"} {
		t.Run(mode, func(t *testing.T) {
			tab := restartAddressTable(t, newPingRecorder())
			b := restartFullAddressBucket(t, tab)
			original := restartAddressNode(t, tab, 50, 0, "172.2.1.1")
			tab.add(original)
			moved := restartMovedNode(original, "172.2.2.1")
			want := moved
			wantCount := 17
			if mode == "reject_full_subnet" {
				tab.add(restartAddressNode(t, tab, 51, 0, "172.2.2.2"))
				tab.add(restartAddressNode(t, tab, 52, 0, "172.2.2.3"))
				want = original
				wantCount = 19
			}
			if mode == "promote_same" || mode == "promote_moved" {
				tab.delete(b.entries[len(b.entries)-1])
				wantCount = 16
				if mode == "promote_same" {
					moved.IP = original.IP
				}
			}

			tab.add(moved)

			found := 0
			for _, list := range [][]*Node{b.entries, b.replacements} {
				for _, n := range list {
					if n.ID == original.ID {
						found++
						if n != want {
							t.Errorf("replacement endpoint: got=%s want=%s", n.addr(), want.addr())
						}
					}
				}
			}
			if found != 1 || tab.ips.Len() != wantCount || b.ips.Len() != wantCount {
				t.Fatalf("identity or reservation transfer: copies=%d table=%d bucket=%d want=%d", found, tab.ips.Len(), b.ips.Len(), wantCount)
			}
			if mode == "promote_same" || mode == "promote_moved" {
				if len(b.replacements) != 0 || b.entries[0] != moved {
					t.Fatal("replacement was not promoted into free entry")
				}
			}
		})
	}
}

func TestRestartPeerReplacementMaturation(t *testing.T) {
	tab := restartAddressTable(t, newPingRecorder())
	b := restartFullAddressBucket(t, tab)
	replacement := restartAddressNode(t, tab, 50, 0, "172.2.1.1")
	tab.add(replacement)
	before := time.Now()

	promoted := tab.replace(b, b.entries[len(b.entries)-1])
	tab.copyLiveNodes()

	if promoted != replacement || replacement.addedAt.Before(before) || tab.db.node(replacement.ID) != nil {
		t.Fatal("newly promoted replacement bypassed the five-minute active-table maturity filter")
	}
	if tab.ips.Len() != 16 || b.ips.Len() != 16 {
		t.Fatal("dead-peer replacement did not transfer exactly one reservation")
	}
}

func TestRestartPeerReplacementCachePreservesAddress(t *testing.T) {
	tab := restartAddressTable(t, newPingRecorder())
	original := restartCacheNode(t, 50)
	original.IP = net.ParseIP("172.2.1.1")
	for i := 0; i < bucketSize; i++ {
		n := restartCacheNode(t, i+1)
		n.IP = net.IPv4(172, 1, byte(i), 1)
		n.sha = original.sha
		tab.add(n)
	}
	if err := tab.db.updateNode(original); err != nil {
		t.Fatal(err)
	}
	if err := tab.db.updateLastPongReceived(original.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	moved := restartMovedNode(original, "172.2.2.1")
	tab.add(moved)

	tab.loadSeedNodes()

	b := tab.bucket(original.sha)
	if len(b.replacements) != 1 || b.replacements[0] != moved || tab.ips.Contains(original.IP) || !tab.ips.Contains(moved.IP) {
		t.Fatal("old cache record replaced the current waiting endpoint or its reservation")
	}
}

type restartAddressTransport struct {
	*pingRecorder
	started chan struct{}
	release chan struct{}
	err     error
	nodes   []*Node
}

func (tr *restartAddressTransport) ping(NodeID, *net.UDPAddr) error {
	close(tr.started)
	<-tr.release
	return tr.err
}

func (tr *restartAddressTransport) findnode(NodeID, *net.UDPAddr, NodeID) ([]*Node, error) {
	close(tr.started)
	<-tr.release
	return tr.nodes, tr.err
}

func TestRestartPeerStaleRevalidation(t *testing.T) {
	for _, mode := range []string{"ip", "port", "refresh", "remove_readd", "current"} {
		for _, responds := range []bool{true, false} {
			t.Run(fmt.Sprintf("%s/responds=%t", mode, responds), func(t *testing.T) {
				tr := &restartAddressTransport{pingRecorder: newPingRecorder(), started: make(chan struct{}), release: make(chan struct{})}
				if !responds {
					tr.err = errTimeout
				}
				tab := restartAddressTable(t, tr)
				original := restartAddressNode(t, tab, 1, 0, "172.0.1.1")
				tab.add(original)
				done := make(chan struct{}, 1)
				go tab.doRevalidate(done)
				<-tr.started
				current := restartMovedNode(original, "172.0.1.1")
				switch mode {
				case "ip":
					current.IP = net.ParseIP("172.0.2.1")
				case "port":
					current.UDP++
				case "remove_readd":
					tab.delete(original)
				case "current":
					current = original
				}
				if mode != "current" {
					tab.add(current)
				}

				close(tr.release)
				<-done

				b := tab.bucket(original.sha)
				if mode == "current" && !responds {
					if len(b.entries) != 0 || tab.ips.Len() != 0 || b.ips.Len() != 0 {
						t.Fatal("current failed probe did not remove the peer and reservation")
					}
				} else if len(b.entries) != 1 || b.entries[0] != current || tab.ips.Len() != 1 || b.ips.Len() != 1 {
					t.Fatal("old revalidation result overwrote or evicted the current peer")
				}
			})
		}
	}
}

func TestRestartPeerStaleFindnode(t *testing.T) {
	for _, mode := range []string{"moved", "current"} {
		for _, responds := range []bool{true, false} {
			t.Run(fmt.Sprintf("%s/responds=%t", mode, responds), func(t *testing.T) {
				tr := &restartAddressTransport{pingRecorder: newPingRecorder(), started: make(chan struct{}), release: make(chan struct{})}
				tab := restartAddressTable(t, tr)
				original := restartAddressNode(t, tab, 1, 0, "172.0.1.1")
				tab.add(original)
				if err := tab.db.updateFindFails(original.ID, 4); err != nil {
					t.Fatal(err)
				}
				if responds {
					tr.nodes = []*Node{restartAddressNode(t, tab, 2, 1, "172.0.3.1")}
				} else {
					tr.err = errTimeout
				}
				reply := make(chan []*Node, 1)
				go tab.findnode(original, NodeID{}, reply)
				<-tr.started
				current := original
				wantFails := 5
				if responds {
					wantFails = 3
				}
				if mode == "moved" {
					current = restartMovedNode(original, "172.0.2.1")
					tab.add(current)
					wantFails = 4
				}

				close(tr.release)
				received := <-reply

				b := tab.bucket(original.sha)
				if mode == "current" && !responds {
					if len(b.entries) != 0 {
						t.Fatal("current fifth failure did not remove peer")
					}
				} else if len(b.entries) != 1 || b.entries[0] != current {
					t.Error("obsolete lookup evicted the current endpoint")
				}
				if tab.db.findFails(original.ID) != wantFails {
					t.Errorf("lookup affected wrong entry's failure count: got=%d want=%d", tab.db.findFails(original.ID), wantFails)
				}
				if len(received) != len(tr.nodes) || (responds && !contains(tab.buckets[1].entries, tr.nodes[0].ID)) {
					t.Fatal("valid neighbors from obsolete lookup were lost")
				}
			})
		}
	}
}

func TestRestartPeerRepeatedDelete(t *testing.T) {
	tab := restartAddressTable(t, newPingRecorder())
	first := restartAddressNode(t, tab, 1, 0, "172.0.1.1")
	second := restartAddressNode(t, tab, 2, 0, "172.0.1.2")
	tab.add(first)
	tab.add(second)
	tab.delete(first)

	tab.delete(first)

	if tab.ips.String() != "{172.0.1.0×1}" || tab.buckets[0].ips.String() != "{172.0.1.0×1}" {
		t.Fatalf("absent peer deletion released another peer's reservation: %s", tab.ips.String())
	}
}
