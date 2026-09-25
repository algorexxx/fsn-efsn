package restart

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/opt"
)

type discoveryPersistenceConfig struct {
	Database        string
	KeyNumber       int
	Bootnodes       []string
	ExpectedPeer    string
	Mode            string
	UnavailableSeed bool
}

type discoveryPersistenceProcess struct {
	done chan error
	log  string
}

func rehearseDiscoveryPersistence(t *testing.T) {
	seed := startConfiguredDiscoveryProbe(t, 1, p2p.Config{NoDial: true})
	community := startConfiguredDiscoveryProbe(t, 3, p2p.Config{NoDial: true, BootstrapNodes: []*discover.Node{seed.server.Self()}})
	root := t.TempDir()
	longConfig := discoveryPersistenceConfig{Database: filepath.Join(root, "mature"), KeyNumber: 2, Bootnodes: []string{seed.server.Self().String()}, ExpectedPeer: community.server.Self().ID.String(), Mode: "learn_mature"}
	longRun := startDiscoveryPersistenceChild(t, root, longConfig)
	awaitDiscoveryCondition(t, "maturing child discovers community node", 60*time.Second, func() bool {
		_, err := os.Stat(longRun.log + ".ready")
		return err == nil
	})
	t.Log("mature child connected; waiting 340 real seconds for the five-minute eligibility period and 30-second persistence tick")

	shortConfig := longConfig
	shortConfig.Database = filepath.Join(root, "short")
	shortConfig.KeyNumber = 4
	shortConfig.Mode = "learn_short"
	shortRun := startDiscoveryPersistenceChild(t, root, shortConfig)
	finishDiscoveryPersistenceChild(t, shortRun, 70*time.Second)
	inspectPersistedDiscoveryPeer(t, shortConfig.Database, community.server.Self(), false)
	shortConfig.Bootnodes = nil
	shortConfig.Mode = "short_cold"
	finishDiscoveryPersistenceChild(t, startDiscoveryPersistenceChild(t, root, shortConfig), 45*time.Second)
	t.Log("short-lived child had pong metadata but no saved endpoint; a separate cold process with no seed remained disconnected")

	finishDiscoveryPersistenceChild(t, longRun, 6*time.Minute)
	inspectPersistedDiscoveryPeer(t, longConfig.Database, community.server.Self(), true)
	seed.server.Stop()
	longConfig.Bootnodes = nil
	longConfig.Mode = "mature_cold"
	longConfig.UnavailableSeed = os.Getenv("FUSION_RESTART_DNS_CACHE") == "1"
	finishDiscoveryPersistenceChild(t, startDiscoveryPersistenceChild(t, root, longConfig), 70*time.Second)
	select {
	case received := <-community.received:
		if received.value != 42 {
			t.Fatalf("unexpected cold-process message: %+v", received)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("community did not receive cold-process probe")
	}
	if longConfig.UnavailableSeed {
		t.Log("separate cold process reconnected from genuine on-disk peers and sent message 42 despite NXDOMAIN bootstrap: no static peers, original seed stopped, community outbound dialing disabled")
	} else {
		t.Log("separate cold process reconnected from its genuine on-disk peer cache and sent message 42: no seeds, no static peers, original seed stopped, community outbound dialing disabled")
	}

	freshConfig := longConfig
	freshConfig.Database = filepath.Join(root, "fresh")
	freshConfig.KeyNumber = 5
	freshConfig.Mode = "fresh_cold"
	finishDiscoveryPersistenceChild(t, startDiscoveryPersistenceChild(t, root, freshConfig), 45*time.Second)
	t.Log("fresh node with no saved or usable configured contacts remained disconnected while the same community node was reachable")
}

func startDiscoveryPersistenceChild(t *testing.T, root string, config discoveryPersistenceConfig) *discoveryPersistenceProcess {
	t.Helper()
	path := filepath.Join(root, config.Mode+".json")
	encoded, err := json.Marshal(config)
	requireNoError(t, err)
	requireNoError(t, os.WriteFile(path, encoded, 0600))
	output, err := os.Create(path + ".log")
	requireNoError(t, err)
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Minute)
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRestartDiscoveryRehearsal$", "-test.v", "-test.timeout=8m")
	command.Env = append(os.Environ(), "FUSION_RESTART_DISCOVERY_PERSISTENCE="+path)
	command.Stdout = output
	command.Stderr = output
	requireNoError(t, command.Start())
	child := &discoveryPersistenceProcess{done: make(chan error, 1), log: path + ".log"}
	go func() {
		child.done <- command.Wait()
		output.Close()
		close(child.done)
	}()
	t.Cleanup(func() {
		cancel()
		<-child.done
	})
	return child
}

func finishDiscoveryPersistenceChild(t *testing.T, child *discoveryPersistenceProcess, timeout time.Duration) {
	t.Helper()
	select {
	case err := <-child.done:
		output, readErr := os.ReadFile(child.log)
		requireNoError(t, readErr)
		if err != nil || strings.Contains(string(output), "WARNING: DATA RACE") || !strings.HasSuffix(strings.TrimSpace(string(output)), "PASS") {
			t.Fatalf("discovery child failed: %v\n%s", err, output)
		}
		t.Logf("cold-process evidence:\n%s", output)
	case <-time.After(timeout):
		t.Fatal("timed out waiting for discovery child")
	}
}

func runDiscoveryPersistenceChild(t *testing.T, path string) {
	encoded, err := os.ReadFile(path)
	requireNoError(t, err)
	var config discoveryPersistenceConfig
	requireNoError(t, json.Unmarshal(encoded, &config))
	if config.KeyNumber < 2 || config.KeyNumber > 5 || !filepath.IsAbs(config.Database) {
		t.Fatal("requires a disposable absolute database path and public test key 2–5")
	}
	peerID, err := discover.HexID(config.ExpectedPeer)
	requireNoError(t, err)
	serverConfig := p2p.Config{NodeDatabase: config.Database}
	for _, url := range config.Bootnodes {
		peer, err := discover.ParseNode(url)
		requireNoError(t, err)
		serverConfig.BootstrapNodes = append(serverConfig.BootstrapNodes, peer)
	}
	if strings.HasSuffix(config.Mode, "_cold") && len(serverConfig.BootstrapNodes) != 0 {
		t.Fatal("cold child must have no supplied endpoint contacts")
	}
	if config.UnavailableSeed {
		startRehearsalDNS(t)
		unavailable, err := discover.ParseBootnode(rehearsalEnode(t, 1, "missing.restart.invalid", 40408))
		requireNoError(t, err)
		serverConfig.BootstrapNodes = append(serverConfig.BootstrapNodes, unavailable)
		t.Log("cold child retains an unresolved bootstrap hostname returning NXDOMAIN")
	}
	probe := startConfiguredDiscoveryProbe(t, config.KeyNumber, serverConfig)
	t.Logf("mode=%s pid=%d bootstrap=%d static=%d database=%s", config.Mode, os.Getpid(), len(serverConfig.BootstrapNodes), len(serverConfig.StaticNodes), config.Database)
	if config.Mode == "short_cold" || config.Mode == "fresh_cold" {
		deadline := time.NewTimer(25 * time.Second)
		defer deadline.Stop()
		tick := time.NewTicker(100 * time.Millisecond)
		defer tick.Stop()
		for {
			select {
			case <-deadline.C:
				t.Log("no connection acquired during 25-second observation")
				return
			case <-tick.C:
				if probe.server.PeerCount() != 0 {
					t.Fatal("cold node unexpectedly connected without saved or configured contacts")
				}
			}
		}
	}
	awaitDiscoveryCondition(t, "child connects to community", 60*time.Second, func() bool { return probe.connected(peerID) })
	t.Log("community connection established")
	if config.Mode == "learn_mature" {
		requireNoError(t, os.WriteFile(path+".log.ready", []byte("connected\n"), 0600))
		for elapsed := time.Duration(0); elapsed < 340*time.Second; elapsed += 20 * time.Second {
			time.Sleep(20 * time.Second)
			if !probe.connected(peerID) {
				t.Fatal("community connection lost during maturation")
			}
		}
		t.Log("340-second real-time peer maturation complete")
		return
	}
	if config.Mode == "learn_short" {
		return
	}
	if config.Mode != "mature_cold" {
		t.Fatal("unknown persistence fixture mode")
	}
	probe.mu.Lock()
	rw := probe.writers[peerID]
	probe.mu.Unlock()
	requireNoError(t, p2p.Send(rw, 0, uint64(42)))
	t.Log("sent message 42 through connection obtained from saved contacts")
}

func inspectPersistedDiscoveryPeer(t *testing.T, path string, peer *discover.Node, wantEndpoint bool) {
	t.Helper()
	database, err := leveldb.OpenFile(path, &opt.Options{ReadOnly: true, ErrorIfMissing: true})
	requireNoError(t, err)
	defer database.Close()
	prefix := append([]byte("n:"), peer.ID[:]...)
	pong, err := database.Get(append(append([]byte(nil), prefix...), []byte(":discover:lastpong")...), nil)
	requireNoError(t, err)
	seconds, bytes := binary.Varint(pong)
	if bytes <= 0 || time.Since(time.Unix(seconds, 0)) > 2*time.Minute {
		t.Fatal("expected recent pong metadata in the closed peer database")
	}
	data, err := database.Get(append(append([]byte(nil), prefix...), []byte(":discover")...), nil)
	if !wantEndpoint {
		if err != leveldb.ErrNotFound {
			t.Fatalf("short session unexpectedly persisted endpoint: %v", err)
		}
		t.Log("closed database contains recent pong metadata but no complete endpoint record")
		return
	}
	requireNoError(t, err)
	var saved discover.Node
	requireNoError(t, rlp.DecodeBytes(data, &saved))
	if saved.String() != peer.String() {
		t.Fatal(fmt.Sprintf("saved community endpoint differs: got=%s want=%s", &saved, peer))
	}
	t.Logf("read-only cold inspection verified exact community endpoint and recent pong: %s", &saved)
}
