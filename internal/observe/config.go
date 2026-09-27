package observe

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math/big"
	"net/url"
	"path/filepath"
	"strings"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/core/types"
)

func ReadConfig(reader io.Reader) (Config, error) {
	var config Config
	data, err := io.ReadAll(io.LimitReader(reader, 1048577))
	if err != nil || len(data) > 1048576 {
		return config, fmt.Errorf("cannot read config within 1 MiB limit")
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&config); err != nil {
		return Config{}, fmt.Errorf("invalid config JSON")
	}
	if decoder.Decode(new(interface{})) != io.EOF {
		return Config{}, fmt.Errorf("config must contain one JSON object")
	}
	return config, ValidateConfig(config)
}

func ValidateConfig(config Config) error {
	chain, ok := new(big.Int).SetString(config.ChainID, 10)
	network, networkOK := new(big.Int).SetString(config.NetworkID, 10)
	if !ok || chain.Sign() <= 0 || !networkOK || network.Sign() < 0 || chain.String() != config.ChainID || network.String() != config.NetworkID {
		return fmt.Errorf("chain and network IDs must be canonical decimal integers")
	}
	if config.Genesis == (common.Hash{}) || config.AnchorNumber == 0 || config.AnchorHash == (common.Hash{}) {
		return fmt.Errorf("explicit genesis and nonzero restart anchor required")
	}
	if len(config.Nodes) < 1 || len(config.Nodes) > 2 || len(config.Tracked) > 64 {
		return fmt.Errorf("one or two nodes and at most 64 tracked transactions required")
	}
	names := make(map[string]bool)
	endpoints := make(map[string]bool)
	owners := make(map[common.Address]bool)
	for _, node := range config.Nodes {
		if strings.TrimSpace(node.Name) == "" || len(node.Name) > 64 || names[node.Name] || node.Wallet == (common.Address{}) {
			return fmt.Errorf("unique node names and explicit monitored wallets required")
		}
		if node.Role != "producer" && node.Role != "verifier" && node.Role != "maintenance" && node.Role != "retired" {
			return fmt.Errorf("unsupported node role")
		}
		if !validEndpoint(node.Endpoint) || endpoints[node.Endpoint] {
			return fmt.Errorf("explicit HTTP(S) URL or absolute IPC endpoint required")
		}
		names[node.Name], owners[node.Wallet] = true, true
		endpoints[node.Endpoint] = true
	}
	seen := make(map[common.Hash]bool)
	for _, raw := range config.Tracked {
		var tx types.Transaction
		if len(raw) > 4096 || tx.UnmarshalBinary(raw) != nil || !tx.Protected() || tx.ChainId().Cmp(chain) != 0 {
			return fmt.Errorf("invalid tracked signed transaction or chain ID")
		}
		owner, err := types.Sender(types.LatestSignerForChainID(chain), &tx)
		if err != nil || !owners[owner] || seen[tx.Hash()] {
			return fmt.Errorf("tracked transaction must have a configured sender and unique hash")
		}
		seen[tx.Hash()] = true
	}
	return nil
}

func validEndpoint(endpoint string) bool {
	if strings.HasPrefix(endpoint, `\\.\pipe\`) || filepath.IsAbs(endpoint) {
		return true
	}
	u, err := url.Parse(endpoint)
	return err == nil && (u.Scheme == "http" || u.Scheme == "https") && u.Host != "" && u.Fragment == ""
}
