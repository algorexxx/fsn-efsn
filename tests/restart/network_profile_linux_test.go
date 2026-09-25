package restart

import (
	"errors"
	"net"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/FusionFoundation/efsn/v5/p2p/nat"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
)

type profileNATCall struct {
	protocol string
	external int
	internal int
	lifetime time.Duration
}

type profileNAT struct {
	mu      sync.Mutex
	ip      net.IP
	failure error
	queries int
	added   chan profileNATCall
	deleted chan profileNATCall
}

func (mapper *profileNAT) ExternalIP() (net.IP, error) {
	mapper.mu.Lock()
	defer mapper.mu.Unlock()
	mapper.queries++
	return append(net.IP(nil), mapper.ip...), mapper.failure
}

func (mapper *profileNAT) AddMapping(protocol string, external, internal int, name string, lifetime time.Duration) error {
	mapper.added <- profileNATCall{protocol, external, internal, lifetime}
	return mapper.failure
}

func (mapper *profileNAT) DeleteMapping(protocol string, external, internal int) error {
	mapper.deleted <- profileNATCall{protocol: protocol, external: external, internal: internal}
	return nil
}

func (mapper *profileNAT) String() string {
	return "isolated-rehearsal-mapper"
}

func TestRestartNetworkProfileRehearsal(t *testing.T) {
	if os.Getenv("FUSION_RESTART_NETWORK_PROFILE") != "1" {
		t.Skip("requires isolated loopback namespace with rehearsal IPv4/IPv6 addresses")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires exactly one enabled loopback interface")
	}
	t.Run("fixed_port_external_ip", rehearseFixedExternalAddress)
	t.Run("wildcard_without_nat", rehearseWildcardAddress)
	t.Run("mapping_and_external_ip_restart", rehearseNATRestart)
	t.Run("mapping_failure_does_not_fail_startup", rehearseNATFailure)
	t.Run("two_ports_one_ipv4_address", rehearseTwoLocalPorts)
	t.Run("ipv6_discovery_and_rlpx", rehearseIPv6Discovery)
	t.Run("tcp_static_without_udp", rehearseTCPWithoutDiscovery)
}

func rehearseFixedExternalAddress(t *testing.T) {
	probe := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, ListenAddr: "172.0.1.1:40408", NAT: nat.ExtIP(net.ParseIP("192.0.2.10"))})
	node := probe.server.Self()
	if node.IP.String() != "192.0.2.10" || node.TCP != 40408 || node.UDP != 40408 || probe.server.ListenAddr != "172.0.1.1:40408" {
		t.Fatalf("wrong fixed-port advertisement: self=%s bind=%s", node, probe.server.ListenAddr)
	}
	t.Log("external advertisement is 192.0.2.10:40408 for TCP and UDP while local bind remains 172.0.1.1:40408; extip does not create a router mapping")
}

func rehearseWildcardAddress(t *testing.T) {
	probe := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, ListenAddr: ":40408"})
	if !probe.server.Self().IP.IsUnspecified() {
		t.Fatalf("unexpected wildcard advertisement: %s", probe.server.Self())
	}
	t.Logf("wildcard bind with no NAT advertises %s; the startup enode is not a usable public contact", probe.server.Self().IP)
}

func rehearseNATRestart(t *testing.T) {
	mapper := &profileNAT{ip: net.ParseIP("192.0.2.10"), added: make(chan profileNATCall, 4), deleted: make(chan profileNATCall, 4)}
	config := p2p.Config{NoDial: true, ListenAddr: "172.0.1.1:40408", NAT: mapper}
	first := startConfiguredDiscoveryProbe(t, 1, config)
	awaitProfileMappings(t, mapper.added, 20*time.Minute)
	identity := first.server.Self().ID
	mapper.mu.Lock()
	mapper.ip = net.ParseIP("192.0.2.20")
	mapper.mu.Unlock()
	if first.server.Self().IP.String() != "192.0.2.10" {
		t.Fatal("external IP unexpectedly refreshed without restart")
	}
	first.server.Stop()
	awaitProfileMappings(t, mapper.deleted, 0)
	second := startConfiguredDiscoveryProbe(t, 1, config)
	awaitProfileMappings(t, mapper.added, 20*time.Minute)
	mapper.mu.Lock()
	queries := mapper.queries
	mapper.mu.Unlock()
	if second.server.Self().IP.String() != "192.0.2.20" || second.server.Self().ID != identity || queries != 2 {
		t.Fatalf("restart did not preserve identity and refresh external address: %s queries=%d", second.server.Self(), queries)
	}
	second.server.Stop()
	awaitProfileMappings(t, mapper.deleted, 0)
	t.Log("recording NAT adapter received matching TCP/UDP map/delete requests; external address queried once per startup; restart refreshed it with unchanged identity; no real router was contacted")
}

func awaitProfileMappings(t *testing.T, calls <-chan profileNATCall, lifetime time.Duration) {
	t.Helper()
	seen := make(map[string]bool)
	for i := 0; i < 2; i++ {
		select {
		case call := <-calls:
			if (call.protocol != "tcp" && call.protocol != "udp") || seen[call.protocol] || call.internal != 40408 || call.external != 40408 || call.lifetime != lifetime {
				t.Fatalf("unexpected NAT call: %+v", call)
			}
			seen[call.protocol] = true
		case <-time.After(3 * time.Second):
			t.Fatal("missing NAT mapping lifecycle call")
		}
	}
}

func rehearseNATFailure(t *testing.T) {
	mapper := &profileNAT{failure: errors.New("synthetic router unavailable"), added: make(chan profileNATCall, 2), deleted: make(chan profileNATCall, 2)}
	probe := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, ListenAddr: "172.0.1.1:40408", NAT: mapper})
	awaitProfileMappings(t, mapper.added, 20*time.Minute)
	if probe.server.Self().IP.String() != "172.0.1.1" {
		t.Fatalf("wrong fallback after NAT error: %s", probe.server.Self())
	}
	probe.server.Stop()
	awaitProfileMappings(t, mapper.deleted, 0)
	t.Log("server starts despite external-IP/mapping failures and advertises local address; running status does not establish public reachability")
}

func rehearseTwoLocalPorts(t *testing.T) {
	first := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, ListenAddr: "127.0.0.1:40408"})
	second := startConfiguredDiscoveryProbe(t, 2, p2p.Config{ListenAddr: "127.0.0.1:40409"})
	second.server.AddPeer(first.server.Self())
	awaitDiscoveryCondition(t, "same-address different-port RLPx connection", 5*time.Second, func() bool { return second.connected(first.server.Self().ID) })
	sendDiscoveryProbe(t, second, first, 61)
	if first.server.Self().TCP != 40408 || first.server.Self().UDP != 40408 || second.server.Self().TCP != 40409 || second.server.Self().UDP != 40409 || first.server.Self().ID == second.server.Self().ID {
		t.Fatal("two-node port or identity separation failed")
	}
	t.Log("two distinct P2P identities share one IP on 40408 and 40409, advertise matching TCP/UDP ports and exchange authenticated RLPx message 61")
}

func rehearseIPv6Discovery(t *testing.T) {
	restrict, err := netutil.ParseNetlist("::1/128")
	requireNoError(t, err)
	key, err := crypto.HexToECDSA("0000000000000000000000000000000000000000000000000000000000000003")
	requireNoError(t, err)
	conn, err := net.ListenUDP("udp6", &net.UDPAddr{IP: net.ParseIP("::1"), Port: 40407})
	requireNoError(t, err)
	seed, err := discover.ListenUDP(conn, discover.Config{PrivateKey: key, NetRestrict: restrict})
	requireNoError(t, err)
	t.Cleanup(seed.Close)
	seedNode := discover.NewNode(seed.Self().ID, seed.Self().IP, seed.Self().UDP, 0)
	first := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, ListenAddr: "[::1]:40408", NetRestrict: restrict, BootstrapNodes: []*discover.Node{seedNode}})
	second := startConfiguredDiscoveryProbe(t, 2, p2p.Config{ListenAddr: "[::1]:40409", NetRestrict: restrict, BootstrapNodes: []*discover.Node{seedNode}})
	awaitDiscoveryCondition(t, "IPv6 RLPx bootstrap", 15*time.Second, func() bool { return second.connected(first.server.Self().ID) })
	sendDiscoveryProbe(t, second, first, 62)
	if first.server.NodeInfo().IP != "::1" || second.server.NodeInfo().IP != "::1" {
		t.Fatal("IPv6 endpoint advertisement was lost")
	}
	t.Log("IPv6 loopback UDP-only seed introduced a nondialing community peer; bracketed endpoints and authenticated RLPx message 62 verified without static or bootstrap TCP fallback")
}

func rehearseTCPWithoutDiscovery(t *testing.T) {
	first := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, NoDiscovery: true, ListenAddr: "127.0.0.1:40408"})
	second := startConfiguredDiscoveryProbe(t, 2, p2p.Config{NoDiscovery: true, ListenAddr: "127.0.0.1:40409"})
	conn, err := net.ListenPacket("udp4", "127.0.0.1:40408")
	requireNoError(t, err)
	defer conn.Close()
	second.server.AddPeer(first.server.Self())
	awaitDiscoveryCondition(t, "TCP static peer without discovery", 5*time.Second, func() bool { return second.connected(first.server.Self().ID) })
	sendDiscoveryProbe(t, second, first, 63)
	if first.server.Self().UDP != 0 || second.server.Self().UDP != 0 {
		t.Fatal("discovery unexpectedly active")
	}
	t.Log("UDP port is unbound with v4/v5 disabled; literal static TCP peer still exchanges RLPx message 63")
}
