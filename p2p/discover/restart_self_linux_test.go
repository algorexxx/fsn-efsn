package discover

import (
	"net"
	"os"
	"testing"
)

func TestRestartDiscoverySelfLive(t *testing.T) {
	if os.Getenv("FUSION_RESTART_ADDRESS_REHEARSAL") != "1" {
		t.Skip("requires isolated loopback namespace with the rehearsal IP aliases")
	}
	interfaces, err := net.Interfaces()
	if err != nil || len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires exactly one enabled loopback interface")
	}
	local := startAddressUDP(t, 1, "172.0.1.1:0")
	seed := startAddressUDP(t, 2, "172.0.2.1:0")
	if err := local.net.ping(seed.self.ID, seed.self.addr()); err != nil {
		t.Fatal(err)
	}
	awaitAddressPeer(t, seed, local.self, "{172.0.1.0×1}")
	awaitAddressPeer(t, local, seed.self, "{172.0.2.0×1}")
	neighbors, err := local.net.findnode(seed.self.ID, seed.self.addr(), local.self.ID)
	if err != nil {
		t.Fatal(err)
	}
	if findNode(neighbors, local.self.ID) == nil {
		t.Fatal("signed neighbor reply did not contain the requesting node")
	}
	reply := make(chan []*Node, 1)
	local.findnode(seed.self, local.self.ID, reply)
	<-reply
	local.mutex.Lock()
	defer local.mutex.Unlock()
	bucket := local.bucket(local.self.sha)
	if findNode(bucket.entries, local.self.ID) != nil || findNode(bucket.replacements, local.self.ID) != nil || local.ips.String() != "{172.0.2.0×1}" {
		t.Fatalf("signed neighbor reply admitted self: entries=%d replacements=%d ips=%s", len(bucket.entries), len(bucket.replacements), local.ips.String())
	}
	t.Log("actual signed UDP neighbor reply contained the requesting identity; table admission excluded it and retained only the real seed's subnet reservation")
}
