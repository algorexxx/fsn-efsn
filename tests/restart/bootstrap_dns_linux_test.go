package restart

import (
	"context"
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/FusionFoundation/efsn/v5/p2p/netutil"
	"golang.org/x/net/dns/dnsmessage"
)

func TestRestartBootstrapDNSRehearsal(t *testing.T) {
	if os.Getenv("FUSION_RESTART_DISCOVERY_REHEARSAL") != "1" {
		t.Skip("requires isolated loopback-only Linux network namespace")
	}
	interfaces, err := net.Interfaces()
	requireNoError(t, err)
	if len(interfaces) != 1 || interfaces[0].Flags&net.FlagLoopback == 0 || interfaces[0].Flags&net.FlagUp == 0 {
		t.Fatal("requires exactly one enabled loopback interface")
	}
	t.Run("toml_operator_command", rehearseBootstrapTOML)
	t.Run("outage_recovery_udp_only_and_move", rehearseBootstrapDNSRecovery)
	t.Run("restricted_answers", rehearseBootstrapDNSRestriction)
	t.Run("shutdown_during_blocked_lookup", rehearseBootstrapDNSCancellation)
}

func rehearseBootstrapTOML(t *testing.T) {
	binary := os.Getenv("FUSION_RESTART_DNS_BINARY")
	if !filepath.IsAbs(binary) {
		t.Fatal("requires absolute path to test efsn executable")
	}
	for _, mode := range []string{"unresolved", "cli_empty_override", "malformed"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			raw := rehearsalEnode(t, 1, "missing.restart.invalid", 40408)
			if mode == "malformed" {
				raw += "?discport=invalid"
			}
			config := filepath.Join(root, "config.toml")
			requireNoError(t, os.WriteFile(config, []byte(fmt.Sprintf("[Node.P2P]\nBootstrapNodes = [%q]\nBootstrapNodesV5 = []\n", raw)), 0600))
			args := []string{"--datadir", filepath.Join(root, "node"), "--config", config, "--bootnodesv5="}
			if mode == "cli_empty_override" {
				args = append(args, "--bootnodesv4=")
			}
			args = append(args, "dumpconfig")
			ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
			defer cancel()
			output, err := exec.CommandContext(ctx, binary, args...).CombinedOutput()
			if mode == "malformed" {
				if err == nil || !strings.Contains(string(output), "invalid discport") {
					t.Fatalf("malformed config: %v\n%s", err, output)
				}
			} else if err != nil {
				t.Fatalf("operator configuration failed: %v\n%s", err, output)
			} else if mode == "unresolved" && !strings.Contains(string(output), raw) {
				t.Fatalf("lost configured hostname: %s", output)
			} else if mode == "cli_empty_override" && !strings.Contains(string(output), "BootstrapNodes = []") {
				t.Fatalf("empty override not retained: %s", output)
			}
			t.Logf("actual efsn dumpconfig mode=%s exit=%v; hostname preservation, override or malformed rejection verified", mode, err)
		})
	}
}

func (dns *rehearsalDNS) fail(name string, code dnsmessage.RCode, drop bool) {
	dns.mu.Lock()
	defer dns.mu.Unlock()
	delete(dns.answers, name+".")
	dns.codes[name+"."] = code
	dns.dropped[name+"."] = drop
}

func (dns *rehearsalDNS) count(name string) int {
	dns.mu.Lock()
	defer dns.mu.Unlock()
	return dns.queries[name+"."]
}

func startBootstrapUDP(t *testing.T, address string) *discover.Table {
	t.Helper()
	key, err := crypto.HexToECDSA(fmt.Sprintf("%064x", 1))
	requireNoError(t, err)
	addr, err := net.ResolveUDPAddr("udp4", address)
	requireNoError(t, err)
	conn, err := net.ListenUDP("udp4", addr)
	requireNoError(t, err)
	restrict, err := netutil.ParseNetlist("127.0.0.0/8")
	requireNoError(t, err)
	table, err := discover.ListenUDP(conn, discover.Config{PrivateKey: key, NetRestrict: restrict})
	requireNoError(t, err)
	t.Cleanup(table.Close)
	return table
}

func rehearseBootstrapDNSRecovery(t *testing.T) {
	dns := startRehearsalDNS(t)
	seed := startBootstrapUDP(t, "127.0.0.1:0")
	community := startConfiguredDiscoveryProbe(t, 3, p2p.Config{NoDial: true, BootstrapNodes: []*discover.Node{seed.Self()}})
	dns.fail("timeout.restart.invalid", 0, true)
	dns.fail("servfail.restart.invalid", dnsmessage.RCodeServerFailure, false)
	raw := rehearsalEnode(t, 1, "community.restart.invalid", 0) + fmt.Sprintf("?discport=%d", seed.Self().UDP)
	bootnodes := discover.BootstrapNodes{}
	for _, url := range []string{raw, rehearsalEnode(t, 6, "timeout.restart.invalid", 40408), rehearsalEnode(t, 7, "servfail.restart.invalid", 40408)} {
		n, err := discover.ParseBootnode(url)
		requireNoError(t, err)
		bootnodes = append(bootnodes, n)
	}
	start := time.Now()
	client := startConfiguredDiscoveryProbe(t, 2, p2p.Config{BootstrapNodes: bootnodes})
	if time.Since(start) > 2*time.Second {
		t.Fatal("DNS blocked startup")
	}
	awaitDiscoveryCondition(t, "all failing DNS contacts queried", 3*time.Second, func() bool {
		return dns.count("community.restart.invalid") > 0 && dns.count("timeout.restart.invalid") > 0 && dns.count("servfail.restart.invalid") > 0
	})
	if client.server.PeerCount() != 0 {
		t.Fatal("client acquired a peer before an available introduction")
	}
	t.Log("startup returned while NXDOMAIN, SERVFAIL and a nonresponding DNS server were present; no initial contacts acquired")
	dns.set("community.restart.invalid", [4]byte{127, 0, 0, 2}, [4]byte{127, 0, 0, 1})
	awaitDiscoveryCondition(t, "DNS retry introduces community through UDP-only seed and second A answer", 30*time.Second, func() bool { return client.connected(community.server.Self().ID) })
	sendDiscoveryProbe(t, client, community, 51)
	if bootnodes[0].String() != raw || bootnodes[0].IP != nil {
		t.Fatal("resolution overwrote configured hostname")
	}
	t.Log("same running client recovered through second A answer and UDP-only seed; reached nondialing community and exchanged message 51")
	port := seed.Self().UDP
	seed.Close()
	moved := startBootstrapUDP(t, fmt.Sprintf("127.0.0.3:%d", port))
	dns.set("community.restart.invalid", [4]byte{127, 0, 0, 3})
	awaitDiscoveryCondition(t, "unchanged identity discovered at moved DNS address", 45*time.Second, func() bool {
		nodes := make([]*discover.Node, 16)
		for _, n := range nodes[:moved.ReadRandomNodes(nodes)] {
			if n.ID == client.server.Self().ID {
				return true
			}
		}
		return false
	})
	t.Log("running client contacted empty UDP seed at changed IP with unchanged key/port, without reparsing configuration or restarting")
	start = time.Now()
	client.server.Stop()
	if time.Since(start) > 2*time.Second {
		t.Fatal("shutdown waited on DNS retry")
	}
	t.Log("shutdown completed within two seconds with failing DNS contacts still configured")
}

func rehearseBootstrapDNSRestriction(t *testing.T) {
	dns := startRehearsalDNS(t)
	dns.set("restricted.restart.invalid", [4]byte{127, 0, 0, 1})
	seed := startBootstrapUDP(t, "127.0.0.1:0")
	n, err := discover.ParseBootnode(rehearsalEnode(t, 1, "restricted.restart.invalid", int(seed.Self().UDP)))
	requireNoError(t, err)
	restrict, err := netutil.ParseNetlist("127.0.0.2/32")
	requireNoError(t, err)
	client := startConfiguredDiscoveryProbe(t, 2, p2p.Config{BootstrapNodes: []*discover.Node{n}, NetRestrict: restrict})
	awaitDiscoveryCondition(t, "restricted name queried", 3*time.Second, func() bool { return dns.count("restricted.restart.invalid") > 0 })
	time.Sleep(time.Second)
	peers := make([]*discover.Node, 16)
	if client.server.PeerCount() != 0 || seed.ReadRandomNodes(peers) != 0 {
		t.Fatal("disallowed DNS answer contacted seed")
	}
	t.Log("DNS answer outside NetRestrict was not contacted or introduced into the peer table")
}

func rehearseBootstrapDNSCancellation(t *testing.T) {
	dns := startRehearsalDNS(t)
	dns.fail("blocked.restart.invalid", 0, true)
	n, err := discover.ParseBootnode(rehearsalEnode(t, 1, "blocked.restart.invalid", 40408))
	requireNoError(t, err)
	client := startConfiguredDiscoveryProbe(t, 2, p2p.Config{BootstrapNodes: []*discover.Node{n}})
	awaitDiscoveryCondition(t, "blocked DNS lookup began", time.Second, func() bool { return dns.count("blocked.restart.invalid") > 0 })
	start := time.Now()
	client.server.Stop()
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Fatalf("shutdown waited for the five-second DNS deadline: %s", elapsed)
	}
	t.Log("shutdown cancelled an in-flight nonresponding DNS lookup within one second")
}
