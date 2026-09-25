package discover

import (
	"fmt"
	"net"
	"os"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
)

func TestRestartPeerAddressLive(t *testing.T) {
	if os.Getenv("FUSION_RESTART_ADDRESS_REHEARSAL") != "1" {
		t.Skip("requires isolated loopback namespace with the rehearsal IP aliases")
	}
	interfaces, err := net.Interfaces()
	if err != nil || len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires exactly one enabled loopback interface")
	}
	local := startAddressUDP(t, 1, "172.0.1.1:0")
	peer := startAddressUDP(t, 2, "172.0.2.1:0")
	if err := peer.net.ping(local.self.ID, local.self.addr()); err != nil {
		t.Fatal(err)
	}
	awaitAddressPeer(t, local, peer.self, "{172.0.2.0×1}")
	port := peer.self.UDP
	peer.Close()
	moved := startAddressUDP(t, 2, fmt.Sprintf("172.0.3.1:%d", port))

	if err := moved.net.ping(local.self.ID, local.self.addr()); err != nil {
		t.Fatal(err)
	}
	awaitAddressPeer(t, local, moved.self, "{172.0.3.0×1}")
	if err := local.net.ping(moved.self.ID, moved.self.addr()); err != nil {
		t.Fatal(err)
	}

	t.Log("real signed UDP ping/pong admitted the same identity at its new /24; old reservation released, new reservation retained; only loopback exists in this namespace")
}

func startAddressUDP(t *testing.T, number int, address string) *Table {
	t.Helper()
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", number))
	if err != nil {
		t.Fatal(err)
	}
	addr, err := net.ResolveUDPAddr("udp4", address)
	if err != nil {
		t.Fatal(err)
	}
	conn, err := net.ListenUDP("udp4", addr)
	if err != nil {
		t.Fatal(err)
	}
	restrict, err := netutil.ParseNetlist("172.0.0.0/16")
	if err != nil {
		t.Fatal(err)
	}
	tab, err := ListenUDP(conn, Config{PrivateKey: key, NetRestrict: restrict})
	if err != nil {
		conn.Close()
		t.Fatal(err)
	}
	t.Cleanup(tab.Close)
	<-tab.initDone
	return tab
}

func awaitAddressPeer(t *testing.T, tab *Table, peer *Node, reservations string) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		tab.mutex.Lock()
		b := tab.bucket(peer.sha)
		found := false
		for _, n := range b.entries {
			if n.ID == peer.ID && n.IP.Equal(peer.IP) && n.UDP == peer.UDP {
				found = true
			}
		}
		tableCounts, bucketCounts := tab.ips.String(), b.ips.String()
		tab.mutex.Unlock()
		if found {
			if tableCounts != reservations || bucketCounts != reservations {
				t.Fatalf("live endpoint changed without reservation transfer: table=%s bucket=%s want=%s", tableCounts, bucketCounts, reservations)
			}
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatalf("live peer was not admitted at %s", peer.addr())
}
