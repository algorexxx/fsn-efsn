package discover

import (
	"bytes"
	"fmt"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/rlp"
	"github.com/naoina/toml"
)

func TestRestartBootstrapConfiguration(t *testing.T) {
	id := restartCacheNode(t, 1).ID.String()
	for _, endpoint := range []string{"missing.restart.invalid:40408", "127.0.0.1:40408", "[::1]:40408", "seed.restart.invalid:0?discport=40408"} {
		t.Run(endpoint, func(t *testing.T) {
			raw := "enode://" + id + "@" + endpoint
			n, err := ParseBootnode(raw)
			if err != nil || n.String() != raw {
				t.Fatalf("parse=%v err=%v", n, err)
			}
			var config struct{ BootstrapNodes BootstrapNodes }
			input := fmt.Sprintf("BootstrapNodes = [%q]\n", raw)
			if err := toml.Unmarshal([]byte(input), &config); err != nil {
				t.Fatal(err)
			}
			encoded, err := toml.Marshal(config)
			if err != nil || !strings.Contains(string(encoded), raw) {
				t.Fatalf("roundtrip=%s err=%v", encoded, err)
			}
			var decoded struct{ BootstrapNodes BootstrapNodes }
			if err := toml.Unmarshal(encoded, &decoded); err != nil || len(decoded.BootstrapNodes) != 1 || decoded.BootstrapNodes[0].String() != raw {
				t.Fatalf("second decode=%v err=%v", decoded, err)
			}
		})
	}
	for _, endpoint := range []string{"missing.restart.invalid:0", ":40408", "bad_name:40408", "-bad.invalid:40408", "bad..invalid:40408", "seed.invalid:65536", "seed.invalid:40408?discport=0", "seed.invalid:40408?discport=3&discport=4", "seed.invalid:40408?other=1", "seed.invalid:40408/path", "seed.invalid:40408#fragment", "0.0.0.0:40408", "224.0.0.1:40408"} {
		if n, err := ParseBootnode("enode://" + id + "@" + endpoint); err == nil {
			t.Fatalf("accepted malformed bootstrap: %s", n)
		}
	}
	if _, err := ParseBootnode("enode://" + strings.Repeat("0", 128) + "@seed.invalid:40408"); err == nil {
		t.Fatal("accepted an invalid public key")
	}
}

func TestRestartBootstrapNodeEncodingUnchanged(t *testing.T) {
	n := restartCacheNode(t, 1)
	legacy := struct {
		IP       []byte
		UDP, TCP uint16
		ID       NodeID
	}{n.IP, n.UDP, n.TCP, n.ID}
	want, err := rlp.EncodeToBytes(legacy)
	if err != nil {
		t.Fatal(err)
	}
	got, err := rlp.EncodeToBytes(n)
	if err != nil || !bytes.Equal(got, want) {
		t.Fatalf("node database encoding changed: %x != %x, %v", got, want, err)
	}
}
