package restart

import (
	"encoding/json"
	"flag"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/cmd/utils"
	"github.com/FusionFoundation/efsn/v5/crypto"
	"github.com/FusionFoundation/efsn/v5/node"
	"github.com/FusionFoundation/efsn/v5/p2p"
	"github.com/FusionFoundation/efsn/v5/p2p/discover"
	"github.com/naoina/toml"
	"github.com/urfave/cli/v2"
)

func TestRestartNetworkConfigInputs(t *testing.T) {
	for _, mode := range []string{"legacy_peer_files", "explicit_empty_peer_lists"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			key, err := crypto.HexToECDSA("0000000000000000000000000000000000000000000000000000000000000001")
			requireNoError(t, err)
			peer := discover.NewNode(discover.PubkeyID(&key.PublicKey), net.ParseIP("192.0.2.10"), 40408, 40408)
			data, err := json.Marshal([]string{peer.String()})
			requireNoError(t, err)
			for _, name := range []string{"static-nodes.json", "trusted-nodes.json"} {
				requireNoError(t, os.WriteFile(filepath.Join(root, name), data, 0600))
			}
			config := node.Config{Name: "efsn", DataDir: root, P2P: p2p.Config{PrivateKey: key}}
			want := 1
			if mode == "explicit_empty_peer_lists" {
				config.P2P.StaticNodes = []*discover.Node{}
				config.P2P.TrustedNodes = []*discover.Node{}
				want = 0
			}

			stack, err := node.New(&config)
			requireNoError(t, err)
			defer stack.Close()

			if len(stack.Server().StaticNodes) != want || len(stack.Server().TrustedNodes) != want || len(config.P2P.StaticNodes) != 0 || len(config.P2P.TrustedNodes) != 0 {
				t.Fatal("effective server peer lists do not match the tested nil/empty input behavior")
			}
			t.Logf("input config contains zero static/trusted entries; effective server loads %d of each from legacy root files; P2P service not started", want)
		})
	}
	for _, explicitNone := range []bool{false, true} {
		name := "omitted_nat_uses_default"
		if explicitNone {
			name = "cli_none_overrides_default"
		}
		t.Run(name, func(t *testing.T) {
			config := struct{ Node node.Config }{Node: node.DefaultConfig}
			requireNoError(t, toml.NewDecoder(strings.NewReader("[Node.P2P]\nBootstrapNodes=[]\nBootstrapNodesV5=[]\n")).Decode(&config))
			set := flag.NewFlagSet(name, flag.ContinueOnError)
			requireNoError(t, utils.NATFlag.Apply(set))
			if explicitNone {
				requireNoError(t, set.Parse([]string{"--nat", "none"}))
			}

			utils.SetP2PConfig(cli.NewContext(cli.NewApp(), set, nil), &config.Node.P2P)

			if (config.Node.P2P.NAT == nil) != explicitNone {
				t.Fatal("omitted TOML NAT or explicit CLI override did not match runtime configuration")
			}
			t.Logf("effective NAT adapter present=%t; no router query or P2P startup performed", config.Node.P2P.NAT != nil)
		})
	}
}
