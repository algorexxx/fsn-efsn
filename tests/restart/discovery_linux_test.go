package restart

import (
	"context"
	"flag"
	"fmt"
	"net"
	"os"
	"os/exec"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/cmd/utils"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/log"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/FusionFoundation/efsn/v5/p2p/discv5"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
	"github.com/urfave/cli/v2"
	"golang.org/x/net/dns/dnsmessage"
)

func TestRestartDiscoveryRehearsal(t *testing.T) {
	if os.Getenv("FUSION_RESTART_DISCOVERY_REHEARSAL") != "1" {
		t.Skip("requires an opt-in isolated loopback-only Linux network namespace")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires exactly one enabled loopback interface")
	}
	log.Root().SetHandler(log.LvlFilterHandler(log.LvlWarn, log.StreamHandler(os.Stderr, log.TerminalFormat(false))))
	if mode := os.Getenv("FUSION_RESTART_DISCOVERY_CLI"); mode != "" {
		rehearseDiscoveryCLI(t, mode)
		return
	}
	t.Run("dns_parse_move_and_multiple_answers", rehearseDiscoveryDNS)
	t.Run("cli_bootstrap_failures", rehearseDiscoveryCLIFailures)
	t.Run("seed_outage_and_static_recovery", rehearseDiscoverySeedOutage)
}

type rehearsalDNS struct {
	mu      sync.Mutex
	answers map[string][][4]byte
}

func startRehearsalDNS(t *testing.T) *rehearsalDNS {
	t.Helper()
	conn, err := net.ListenPacket("udp4", "127.0.0.1:0")
	requireNoError(t, err)
	dns := &rehearsalDNS{answers: make(map[string][][4]byte)}
	done := make(chan struct{})
	go func() {
		defer close(done)
		buf := make([]byte, 4096)
		for {
			n, addr, err := conn.ReadFrom(buf)
			if err != nil {
				return
			}
			var request dnsmessage.Message
			if err := request.Unpack(buf[:n]); err != nil {
				t.Errorf("decode test DNS request: %v", err)
				return
			}
			response := dnsmessage.Message{Header: dnsmessage.Header{ID: request.ID, Response: true, Authoritative: true, RecursionDesired: request.RecursionDesired, RecursionAvailable: true}, Questions: request.Questions}
			for _, question := range request.Questions {
				dns.mu.Lock()
				answers, found := dns.answers[question.Name.String()]
				dns.mu.Unlock()
				if !found {
					response.Header.RCode = dnsmessage.RCodeNameError
					continue
				}
				if question.Type == dnsmessage.TypeA {
					for _, ip := range answers {
						response.Answers = append(response.Answers, dnsmessage.Resource{Header: dnsmessage.ResourceHeader{Name: question.Name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET, TTL: 0}, Body: &dnsmessage.AResource{A: ip}})
					}
				}
			}
			encoded, err := response.Pack()
			if err != nil {
				t.Errorf("encode test DNS response: %v", err)
				return
			}
			if _, err := conn.WriteTo(encoded, addr); err != nil {
				return
			}
		}
	}()
	previous := net.DefaultResolver
	net.DefaultResolver = &net.Resolver{PreferGo: true, Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, "udp4", conn.LocalAddr().String())
	}}
	t.Cleanup(func() {
		net.DefaultResolver = previous
		conn.Close()
		<-done
	})
	return dns
}

func (dns *rehearsalDNS) set(name string, addresses ...[4]byte) {
	dns.mu.Lock()
	defer dns.mu.Unlock()
	dns.answers[name+"."] = addresses
}

func rehearsalEnode(t *testing.T, keyNumber int, host string, port int) string {
	t.Helper()
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", keyNumber))
	requireNoError(t, err)
	return fmt.Sprintf("enode://%s@%s:%d", discover.PubkeyID(&key.PublicKey), host, port)
}

func rehearseDiscoveryDNS(t *testing.T) {
	dns := startRehearsalDNS(t)
	dns.set("seed.restart.invalid", [4]byte{127, 0, 0, 2})
	listener, err := net.Listen("tcp4", "127.0.0.3:0")
	requireNoError(t, err)
	defer listener.Close()
	url := rehearsalEnode(t, 1, "seed.restart.invalid", listener.Addr().(*net.TCPAddr).Port)
	original, err := discover.ParseNode(url)
	requireNoError(t, err)
	if !original.IP.Equal(net.ParseIP("127.0.0.2")) || strings.Contains(original.String(), "seed.restart.invalid") {
		t.Fatalf("unexpected original endpoint: %s", original)
	}
	dns.set("seed.restart.invalid", [4]byte{127, 0, 0, 3})
	updated, err := discover.ParseNode(url)
	requireNoError(t, err)
	if !updated.IP.Equal(net.ParseIP("127.0.0.3")) || !original.IP.Equal(net.ParseIP("127.0.0.2")) || updated.ID != original.ID {
		t.Fatalf("DNS move should require parsing again and preserve identity: old=%s new=%s", original, updated)
	}
	dns.set("seed.restart.invalid", [4]byte{127, 0, 0, 2}, [4]byte{127, 0, 0, 3})
	multiple, err := discover.ParseNode(url)
	requireNoError(t, err)
	if !multiple.IP.Equal(net.ParseIP("127.0.0.2")) {
		t.Fatalf("expected first of the two IPv4 answers, got %s", multiple.IP)
	}
	dialer := p2p.TCPDialer{Dialer: &net.Dialer{Timeout: time.Second}}
	if conn, err := dialer.Dial(multiple); err == nil {
		conn.Close()
		t.Fatal("dial unexpectedly fell back to the second DNS answer")
	}
	conn, err := dialer.Dial(updated)
	requireNoError(t, err)
	conn.Close()
	if _, err := discover.ParseNode(rehearsalEnode(t, 1, "missing.restart.invalid", 40408)); err == nil || err.Error() != "invalid host" {
		t.Fatalf("missing v4 DNS error: %v", err)
	}
	if _, err := discv5.ParseNode(url); err == nil || err.Error() != "invalid IP address" {
		t.Fatalf("v5 DNS rejection: %v", err)
	}
	t.Log("v4 resolves once, keeps one IP, loses hostname and does not dial the second answer; reparse moves IP with identical node ID; v5 rejects DNS")
}

func rehearseDiscoveryCLIFailures(t *testing.T) {
	for _, mode := range []string{"healthy", "bad_then_good", "good_then_bad", "all_bad", "nodiscover_bad", "empty", "nodiscover_empty", "malformed"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartDiscoveryRehearsal$", "-test.v")
			command.Env = append(os.Environ(), "FUSION_RESTART_DISCOVERY_CLI="+mode)
			output, err := command.CombinedOutput()
			if mode == "healthy" || mode == "empty" || mode == "nodiscover_empty" {
				if err != nil || !strings.Contains(string(output), "bootstrap configuration returned") {
					t.Fatalf("expected successful configuration: %v\n%s", err, output)
				}
			} else {
				exit, ok := err.(*exec.ExitError)
				if !ok || exit.ExitCode() != 1 || !strings.Contains(string(output), "Bootstrap URL invalid") || strings.Contains(string(output), "bootstrap configuration returned") {
					t.Fatalf("expected fatal bootstrap configuration error: %v\n%s", err, output)
				}
			}
			t.Logf("%s:\n%s", mode, output)
		})
	}
}

func rehearseDiscoveryCLI(t *testing.T, mode string) {
	dns := startRehearsalDNS(t)
	dns.set("seed.restart.invalid", [4]byte{127, 0, 0, 2})
	good := rehearsalEnode(t, 1, "seed.restart.invalid", 40408)
	bad := rehearsalEnode(t, 2, "missing.restart.invalid", 40408)
	urls := map[string]string{"healthy": good, "bad_then_good": bad + "," + good, "good_then_bad": good + "," + bad, "all_bad": bad, "nodiscover_bad": bad, "empty": "", "nodiscover_empty": "", "malformed": "not-an-enode"}
	value, found := urls[mode]
	if !found {
		t.Fatal("unknown CLI fixture")
	}
	set := flag.NewFlagSet("discovery-rehearsal", flag.ContinueOnError)
	for _, option := range []cli.Flag{utils.BootnodesV4Flag, utils.BootnodesV5Flag, utils.NoDiscoverFlag} {
		requireNoError(t, option.Apply(set))
	}
	args := []string{"--bootnodesv4=" + value, "--bootnodesv5="}
	if strings.HasPrefix(mode, "nodiscover_") {
		args = append(args, "--nodiscover")
	}
	requireNoError(t, set.Parse(args))
	cfg := &p2p.Config{MaxPeers: 8}
	utils.SetP2PConfig(cli.NewContext(cli.NewApp(), set, nil), cfg)
	if (mode == "empty" || mode == "nodiscover_empty") && (cfg.BootstrapNodes == nil || len(cfg.BootstrapNodes) != 0) {
		t.Fatal("explicit empty list was not retained")
	}
	t.Logf("bootstrap configuration returned: v4=%d v5=%d discoveryDisabled=%t", len(cfg.BootstrapNodes), len(cfg.BootstrapNodesV5), cfg.NoDiscovery)
}

type discoveryProbe struct {
	server   *p2p.Server
	mu       sync.Mutex
	writers  map[discover.NodeID]p2p.MsgReadWriter
	received chan discoveryProbeMessage
}

type discoveryProbeMessage struct {
	from  discover.NodeID
	value uint64
}

func startDiscoveryProbe(t *testing.T, keyNumber int, bootnodes []*discover.Node) *discoveryProbe {
	t.Helper()
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", keyNumber))
	requireNoError(t, err)
	restrict, err := netutil.ParseNetlist("127.0.0.0/8")
	requireNoError(t, err)
	reservation, err := net.Listen("tcp4", "127.0.0.1:0")
	requireNoError(t, err)
	listenAddr := reservation.Addr().String()
	requireNoError(t, reservation.Close())
	probe := &discoveryProbe{writers: make(map[discover.NodeID]p2p.MsgReadWriter), received: make(chan discoveryProbeMessage, 32)}
	probe.server = &p2p.Server{Config: p2p.Config{PrivateKey: key, Name: "restart-discovery-rehearsal", MaxPeers: 12, DialRatio: 2, ListenAddr: listenAddr, BootstrapNodes: bootnodes, NetRestrict: restrict, Protocols: []p2p.Protocol{{Name: "restartprobe", Version: 1, Length: 1, Run: probe.run}}}}
	requireNoError(t, probe.server.Start())
	t.Cleanup(probe.server.Stop)
	return probe
}

func (probe *discoveryProbe) run(peer *p2p.Peer, rw p2p.MsgReadWriter) error {
	probe.mu.Lock()
	probe.writers[peer.ID()] = rw
	probe.mu.Unlock()
	defer func() {
		probe.mu.Lock()
		delete(probe.writers, peer.ID())
		probe.mu.Unlock()
	}()
	for {
		msg, err := rw.ReadMsg()
		if err != nil {
			return err
		}
		var value uint64
		if err := msg.Decode(&value); err != nil {
			return err
		}
		probe.received <- discoveryProbeMessage{from: peer.ID(), value: value}
	}
}

func (probe *discoveryProbe) connected(id discover.NodeID) bool {
	probe.mu.Lock()
	defer probe.mu.Unlock()
	return probe.writers[id] != nil
}

func awaitDiscoveryCondition(t *testing.T, description string, timeout time.Duration, condition func() bool) {
	t.Helper()
	deadline := time.NewTimer(timeout)
	defer deadline.Stop()
	tick := time.NewTicker(50 * time.Millisecond)
	defer tick.Stop()
	for !condition() {
		select {
		case <-deadline.C:
			t.Fatal("timed out: " + description)
		case <-tick.C:
		}
	}
}

func sendDiscoveryProbe(t *testing.T, from, to *discoveryProbe, value uint64) {
	t.Helper()
	from.mu.Lock()
	rw := from.writers[to.server.Self().ID]
	from.mu.Unlock()
	if rw == nil {
		t.Fatal("probe peer not connected")
	}
	done := make(chan error, 1)
	go func() { done <- p2p.Send(rw, 0, value) }()
	select {
	case err := <-done:
		requireNoError(t, err)
	case <-time.After(3 * time.Second):
		t.Fatal("probe send stalled")
	}
	select {
	case received := <-to.received:
		if received != (discoveryProbeMessage{from: from.server.Self().ID, value: value}) {
			t.Fatalf("unexpected probe: %+v", received)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("probe receive stalled")
	}
}

func rehearseDiscoverySeedOutage(t *testing.T) {
	seed := startDiscoveryProbe(t, 1, nil)
	bootnodes := []*discover.Node{seed.server.Self()}
	seedID := seed.server.Self().ID
	first := startDiscoveryProbe(t, 2, bootnodes)
	second := startDiscoveryProbe(t, 3, bootnodes)
	awaitDiscoveryCondition(t, "two nodes discover each other through the seed", 90*time.Second, func() bool {
		return first.connected(second.server.Self().ID) && second.connected(first.server.Self().ID)
	})
	sendDiscoveryProbe(t, first, second, 1)
	t.Log("two fresh nodes discovered each other through one seed and exchanged an authenticated RLPx subprotocol message")
	seed.server.Stop()
	awaitDiscoveryCondition(t, "seed disconnect", 5*time.Second, func() bool {
		return !first.connected(seedID) && !second.connected(seedID)
	})
	sendDiscoveryProbe(t, first, second, 2)
	stranded := startDiscoveryProbe(t, 4, bootnodes)
	empty := startDiscoveryProbe(t, 5, nil)
	time.Sleep(25 * time.Second)
	if stranded.server.PeerCount() != 0 || empty.server.PeerCount() != 0 {
		t.Fatal("fresh isolated nodes acquired peers without a reachable first contact")
	}
	sendDiscoveryProbe(t, second, first, 3)
	t.Log("existing peers still exchange messages after 25 seconds with seed stopped; fresh nodes with an offline seed or no seeds remain disconnected")
	stranded.server.AddPeer(first.server.Self())
	empty.server.AddPeer(second.server.Self())
	awaitDiscoveryCondition(t, "static peer fallback", 15*time.Second, func() bool {
		return stranded.connected(first.server.Self().ID) && empty.connected(second.server.Self().ID)
	})
	sendDiscoveryProbe(t, stranded, first, 4)
	sendDiscoveryProbe(t, empty, second, 5)
	t.Log("both fresh nodes recovered through a literal-IP static peer without restarting or restoring the seed")
}
