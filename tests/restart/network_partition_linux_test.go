package restart

import (
	"context"
	"encoding/json"
	"net"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
)

func TestRestartNetworkPartitionRehearsal(t *testing.T) {
	requirePartitionNamespace(t)
	t.Run("short_loss_retains_tcp_connection", rehearseShortPacketLoss)
	t.Run("long_static_partition", func(t *testing.T) { rehearseLongStaticPartition(t, false) })
	t.Run("one_way_static_partition", func(t *testing.T) { rehearseLongStaticPartition(t, true) })
	t.Run("dynamic_peers_and_seed_recover", rehearseDynamicPartition)
	t.Run("fresh_dns_contact_udp_blocked", rehearseDiscoveryUDPPartition)
}

func requirePartitionNamespace(t *testing.T) {
	t.Helper()
	if os.Getenv("FUSION_RESTART_NETWORK_PARTITION") != "1" {
		t.Skip("requires root inside a disposable loopback-only network namespace")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if os.Geteuid() != 0 || len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires root and exactly one enabled loopback interface")
	}
	current, err := os.Readlink("/proc/self/ns/net")
	requireNoError(t, err)
	initial, err := os.Readlink("/proc/1/ns/net")
	requireNoError(t, err)
	if current == initial {
		t.Fatal("refusing to change the initial network namespace")
	}
}

func runPartitionTC(t *testing.T, args ...string) []byte {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	output, err := exec.CommandContext(ctx, "/usr/sbin/tc", args...).CombinedOutput()
	if err != nil {
		t.Fatalf("tc %v: %v\n%s", args, err, output)
	}
	return output
}

func dropRehearsalPackets(t *testing.T, matches ...string) func() {
	t.Helper()
	runPartitionTC(t, "qdisc", "add", "dev", "lo", "root", "handle", "1:", "prio", "bands", "3", "priomap", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0")
	active := true
	t.Cleanup(func() {
		if active {
			runPartitionTC(t, "qdisc", "del", "dev", "lo", "root")
		}
	})
	runPartitionTC(t, "qdisc", "add", "dev", "lo", "parent", "1:3", "handle", "30:", "netem", "loss", "100%")
	args := []string{"filter", "add", "dev", "lo", "protocol", "ip", "parent", "1:", "priority", "1", "u32"}
	args = append(args, matches...)
	args = append(args, "flowid", "1:3")
	runPartitionTC(t, args...)
	t.Logf("kernel packet-loss filter: %v", matches)
	return func() {
		t.Helper()
		stats := runPartitionTC(t, "-s", "-j", "qdisc", "show", "dev", "lo")
		var queues []struct {
			Kind  string `json:"kind"`
			Drops uint64 `json:"drops"`
		}
		requireNoError(t, json.Unmarshal(stats, &queues))
		var drops uint64
		for _, queue := range queues {
			if queue.Kind == "netem" {
				drops += queue.Drops
			}
		}
		runPartitionTC(t, "qdisc", "del", "dev", "lo", "root")
		active = false
		if drops == 0 {
			t.Fatal("partition did not drop any packets")
		}
		t.Logf("healed partition; netem dropped=%d; qdisc statistics=%s", drops, stats)
	}
}

func awaitPartitionPeers(t *testing.T, first, second *discoveryProbe, connected bool, timeout time.Duration) {
	t.Helper()
	awaitDiscoveryCondition(t, "both RLPx peers reach expected connection state", timeout, func() bool {
		return first.connected(second.server.Self().ID) == connected && second.connected(first.server.Self().ID) == connected
	})
}

func partitionWriter(probe, peer *discoveryProbe) p2p.MsgReadWriter {
	probe.mu.Lock()
	defer probe.mu.Unlock()
	return probe.writers[peer.server.Self().ID]
}

func rehearseShortPacketLoss(t *testing.T) {
	first := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, NoDiscovery: true})
	second := startConfiguredDiscoveryProbe(t, 2, p2p.Config{NoDiscovery: true, StaticNodes: []*discover.Node{first.server.Self()}})
	awaitPartitionPeers(t, first, second, true, 5*time.Second)
	sendDiscoveryProbe(t, first, second, 71)
	firstWriter, secondWriter := partitionWriter(first, second), partitionWriter(second, first)
	heal := dropRehearsalPackets(t, "match", "ip", "dst", "127.0.0.0/8")
	done := make(chan error, 1)
	go func() { done <- p2p.Send(secondWriter, 0, uint64(72)) }()
	select {
	case err := <-done:
		requireNoError(t, err)
	case <-time.After(3 * time.Second):
		t.Fatal("small buffered TCP write unexpectedly stalled")
	}
	select {
	case received := <-first.received:
		t.Fatalf("message crossed complete packet loss: %+v", received)
	case <-time.After(3 * time.Second):
	}
	heal()
	select {
	case received := <-first.received:
		if received != (discoveryProbeMessage{from: second.server.Self().ID, value: 72}) {
			t.Fatalf("unexpected retransmitted message: %+v", received)
		}
	case <-time.After(10 * time.Second):
		t.Fatal("buffered message did not arrive after healing")
	}
	if partitionWriter(first, second) != firstWriter || partitionWriter(second, first) != secondWriter {
		t.Fatal("short outage replaced the original protocol connection")
	}
	sendDiscoveryProbe(t, first, second, 73)
	t.Log("three-second silent loss: successful local write did not establish delivery; TCP retransmitted message 72 after healing and both original protocol connections survived")
}

func rehearseLongStaticPartition(t *testing.T, oneWay bool) {
	first := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true, NoDiscovery: true, ListenAddr: "127.0.0.2:40408"})
	second := startConfiguredDiscoveryProbe(t, 2, p2p.Config{NoDiscovery: true, StaticNodes: []*discover.Node{first.server.Self()}})
	awaitPartitionPeers(t, first, second, true, 5*time.Second)
	sendDiscoveryProbe(t, second, first, 74)
	firstWriter, secondWriter := partitionWriter(first, second), partitionWriter(second, first)
	destination := "127.0.0.0/8"
	if oneWay {
		destination = "127.0.0.2/32"
	}
	heal := dropRehearsalPackets(t, "match", "ip", "dst", destination)
	started := time.Now()
	if oneWay {
		sendDiscoveryProbe(t, first, second, 75)
		t.Log("reverse-direction authenticated message 75 arrived while packets toward 127.0.0.2 were being dropped")
	}
	awaitPartitionPeers(t, first, second, false, 50*time.Second)
	t.Logf("both static peer sessions detected silent loss after %s", time.Since(started))
	if remaining := 45*time.Second - time.Since(started); remaining > 0 {
		time.Sleep(remaining)
	}
	if first.server.PeerCount() != 0 || second.server.PeerCount() != 0 {
		t.Fatal("static peers connected during packet loss")
	}
	heal()
	recovered := time.Now()
	awaitPartitionPeers(t, first, second, true, 90*time.Second)
	if partitionWriter(first, second) == firstWriter || partitionWriter(second, first) == secondWriter {
		t.Fatal("long outage did not replace both protocol connections")
	}
	sendDiscoveryProbe(t, second, first, 76)
	sendDiscoveryProbe(t, first, second, 77)
	t.Logf("static peers automatically reconnected in %s after 45-second partition; exchanged messages 76/77 without AddPeer, manual disconnect or restart; discovery remained disabled", time.Since(recovered))
}

func rehearseDynamicPartition(t *testing.T) {
	seed := startBootstrapUDP(t, "127.0.0.1:40407")
	contact := discover.NewNode(seed.Self().ID, seed.Self().IP, seed.Self().UDP, 0)
	first := startConfiguredDiscoveryProbe(t, 2, p2p.Config{BootstrapNodes: []*discover.Node{contact}})
	second := startConfiguredDiscoveryProbe(t, 3, p2p.Config{BootstrapNodes: []*discover.Node{contact}})
	awaitPartitionPeers(t, first, second, true, 20*time.Second)
	sendDiscoveryProbe(t, second, first, 78)
	heal := dropRehearsalPackets(t, "match", "ip", "dst", "127.0.0.0/8")
	started := time.Now()
	awaitPartitionPeers(t, first, second, false, 50*time.Second)
	t.Logf("both dynamically introduced peer sessions detected silent loss after %s", time.Since(started))
	if remaining := 45*time.Second - time.Since(started); remaining > 0 {
		time.Sleep(remaining)
	}
	if first.server.PeerCount() != 0 || second.server.PeerCount() != 0 {
		t.Fatal("dynamic peers connected during packet loss")
	}
	heal()
	recovered := time.Now()
	awaitPartitionPeers(t, first, second, true, 90*time.Second)
	sendDiscoveryProbe(t, second, first, 79)
	sendDiscoveryProbe(t, first, second, 80)
	t.Logf("dynamic peers automatically reconnected in %s with original UDP-only seed still running; messages 79/80 verified; no static peers, seed TCP service, AddPeer, manual disconnect or restart", time.Since(recovered))
}

func rehearseDiscoveryUDPPartition(t *testing.T) {
	dns := startRehearsalDNS(t)
	dns.set("partition.restart.invalid", [4]byte{127, 0, 0, 1})
	seed := startBootstrapUDP(t, "127.0.0.1:40407")
	contact := discover.NewNode(seed.Self().ID, seed.Self().IP, seed.Self().UDP, 0)
	community := startConfiguredDiscoveryProbe(t, 2, p2p.Config{BootstrapNodes: []*discover.Node{contact}})
	awaitDiscoveryCondition(t, "community is known to UDP seed", 10*time.Second, func() bool {
		return seed.Resolve(community.server.Self().ID) != nil
	})
	heal := dropRehearsalPackets(t, "match", "ip", "protocol", "17", "0xff", "match", "ip", "dport", "40407", "0xffff")
	bootstrap, err := discover.ParseBootnode(rehearsalEnode(t, 1, "partition.restart.invalid", 0) + "?discport=40407")
	requireNoError(t, err)
	client := startConfiguredDiscoveryProbe(t, 3, p2p.Config{BootstrapNodes: []*discover.Node{bootstrap}})
	awaitDiscoveryCondition(t, "DNS resolves despite discovery UDP loss", 3*time.Second, func() bool { return dns.count("partition.restart.invalid") > 0 })
	control := startConfiguredDiscoveryProbe(t, 4, p2p.Config{NoDiscovery: true, StaticNodes: []*discover.Node{community.server.Self()}})
	awaitPartitionPeers(t, control, community, true, 5*time.Second)
	sendDiscoveryProbe(t, control, community, 81)
	time.Sleep(12 * time.Second)
	if client.server.PeerCount() != 0 {
		t.Fatal("fresh client found a peer through blocked discovery")
	}
	t.Logf("DNS answered %d questions and independent static TCP message 81 arrived, but fresh client stayed peerless while seed UDP was blocked", dns.count("partition.restart.invalid"))
	heal()
	recovered := time.Now()
	awaitPartitionPeers(t, client, community, true, 90*time.Second)
	sendDiscoveryProbe(t, client, community, 82)
	t.Logf("same fresh client automatically discovered community in %s after UDP returned; authenticated message 82 verified without static peer, seed TCP service or restart", time.Since(recovered))
}
