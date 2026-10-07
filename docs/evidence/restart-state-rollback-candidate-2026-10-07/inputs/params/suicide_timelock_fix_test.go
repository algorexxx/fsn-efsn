package params

import (
	"encoding/json"
	"math/big"
	"reflect"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
)

func TestSuicideTimeLockFixRules(t *testing.T) {
	cases := []struct {
		name   string
		fork   *big.Int
		block  *big.Int
		active bool
	}{
		{"unscheduled", nil, big.NewInt(101), false},
		{"missing_block", big.NewInt(100), nil, false},
		{"before", big.NewInt(100), big.NewInt(99), false},
		{"boundary", big.NewInt(100), big.NewInt(100), true},
		{"after", big.NewInt(100), big.NewInt(101), true},
		{"custom_genesis", big.NewInt(0), big.NewInt(0), true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			config := &ChainConfig{SuicideTimeLockFixBlock: tc.fork}

			actual := config.Rules(tc.block).IsSuicideTimeLockFix

			if actual != tc.active {
				t.Fatalf("active = %v, want %v", actual, tc.active)
			}
		})
	}
}

func TestResolveSuicideTimeLockFix(t *testing.T) {
	original := MainnetChainConfig.SuicideTimeLockFixBlock
	t.Cleanup(func() { MainnetChainConfig.SuicideTimeLockFixBlock = original })
	cases := []struct {
		name     string
		approved *big.Int
		config   *ChainConfig
		genesis  common.Hash
		head     uint64
		want     *big.Int
		wantErr  string
	}{
		{"missing_config", nil, nil, common.Hash{}, 0, nil, "suicide time-lock fix: chain configuration required"},
		{"unselected_mainnet", nil, &ChainConfig{ChainID: big.NewInt(32659)}, MainnetGenesisHash, 101, nil, ""},
		{"unapproved_mainnet", nil, &ChainConfig{ChainID: big.NewInt(32659), SuicideTimeLockFixBlock: big.NewInt(100)}, MainnetGenesisHash, 99, nil, "suicide time-lock fix: no mainnet activation is approved in this build"},
		{"legacy_before", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659)}, MainnetGenesisHash, 99, big.NewInt(100), ""},
		{"legacy_boundary", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659)}, MainnetGenesisHash, 100, nil, "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{"legacy_after", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659)}, MainnetGenesisHash, 101, nil, "suicide time-lock fix: missing mainnet activation at or after its boundary"},
		{"same_after", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659), SuicideTimeLockFixBlock: big.NewInt(100)}, MainnetGenesisHash, 101, big.NewInt(100), ""},
		{"different_before", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659), SuicideTimeLockFixBlock: big.NewInt(101)}, MainnetGenesisHash, 99, nil, "suicide time-lock fix: mainnet activation differs from this build"},
		{"different_after", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659), SuicideTimeLockFixBlock: big.NewInt(101)}, MainnetGenesisHash, 101, nil, "suicide time-lock fix: mainnet activation differs from this build"},
		{"wrong_chain_id", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(1)}, MainnetGenesisHash, 99, nil, "suicide time-lock fix: mainnet chain identity mismatch"},
		{"missing_chain_id", big.NewInt(100), &ChainConfig{}, MainnetGenesisHash, 99, nil, "suicide time-lock fix: mainnet chain identity mismatch"},
		{"same_id_other_genesis", big.NewInt(100), &ChainConfig{ChainID: big.NewInt(32659)}, common.Hash{}, 101, nil, ""},
		{"custom_schedule", big.NewInt(100), &ChainConfig{SuicideTimeLockFixBlock: big.NewInt(3)}, common.Hash{}, 101, big.NewInt(3), ""},
		{"negative_schedule", nil, &ChainConfig{SuicideTimeLockFixBlock: big.NewInt(-1)}, common.Hash{}, 0, nil, "suicide time-lock fix: activation height must fit uint64"},
		{"oversized_schedule", nil, &ChainConfig{SuicideTimeLockFixBlock: new(big.Int).Lsh(big.NewInt(1), 64)}, common.Hash{}, 0, nil, "suicide time-lock fix: activation height must fit uint64"},
		{"invalid_mainnet_zero", big.NewInt(0), &ChainConfig{ChainID: big.NewInt(32659)}, MainnetGenesisHash, 0, nil, "suicide time-lock fix: invalid approved mainnet activation"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			MainnetChainConfig.SuicideTimeLockFixBlock = tc.approved
			before, _ := json.Marshal(tc.config)

			actual, err := ResolveSuicideTimeLockFix(tc.config, tc.genesis, tc.head)
			after, _ := json.Marshal(tc.config)

			if string(before) != string(after) {
				t.Fatal("resolver changed its input")
			}
			if tc.wantErr != "" {
				if err == nil || err.Error() != tc.wantErr || actual != nil {
					t.Fatalf("result = %v, %v; want nil, %s", actual, err, tc.wantErr)
				}
				return
			}
			if err != nil || actual == nil {
				t.Fatalf("resolve: %v", err)
			}
			if !reflect.DeepEqual(actual.SuicideTimeLockFixBlock, tc.want) {
				t.Fatalf("schedule = %v, want %v", actual.SuicideTimeLockFixBlock, tc.want)
			}
			if actual == tc.config || (actual.SuicideTimeLockFixBlock != nil && (actual.SuicideTimeLockFixBlock == tc.config.SuicideTimeLockFixBlock || actual.SuicideTimeLockFixBlock == tc.approved)) {
				t.Fatal("resolved configuration or schedule aliases the input")
			}
		})
	}
}

func TestSuicideTimeLockFixCompatibility(t *testing.T) {
	cases := []struct {
		name string
		old  *big.Int
		next *big.Int
		head uint64
		want *ConfigCompatError
	}{
		{"future_add", nil, big.NewInt(100), 99, nil},
		{"same_after", big.NewInt(100), big.NewInt(100), 101, nil},
		{"boundary_add", nil, big.NewInt(100), 100, &ConfigCompatError{"Suicide time-lock fix block", nil, big.NewInt(100), 99}},
		{"after_remove", big.NewInt(100), nil, 101, &ConfigCompatError{"Suicide time-lock fix block", big.NewInt(100), nil, 99}},
		{"after_move", big.NewInt(100), big.NewInt(200), 101, &ConfigCompatError{"Suicide time-lock fix block", big.NewInt(100), big.NewInt(200), 99}},
		{"zero_rewind", nil, big.NewInt(1), 1, &ConfigCompatError{"Suicide time-lock fix block", nil, big.NewInt(1), 0}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			stored := &ChainConfig{SuicideTimeLockFixBlock: tc.old}
			next := &ChainConfig{SuicideTimeLockFixBlock: tc.next}

			actual := stored.CheckCompatible(next, tc.head)

			if !reflect.DeepEqual(actual, tc.want) {
				t.Fatalf("compatibility = %#v, want %#v", actual, tc.want)
			}
		})
	}
}

func TestSuicideTimeLockFixConfigurationJSON(t *testing.T) {
	config := &ChainConfig{ChainID: big.NewInt(32659), SuicideTimeLockFixBlock: big.NewInt(100)}
	want := `{"chainId":32659,"eip150Hash":"0x0000000000000000000000000000000000000000000000000000000000000000","suicideTimeLockFixBlock":100}`

	actual, err := json.Marshal(config)

	if err != nil || string(actual) != want {
		t.Fatalf("JSON = %s, %v; want %s", actual, err, want)
	}
}
