package main

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/FusionFoundation/efsn/v5/common"
	"github.com/FusionFoundation/efsn/v5/internal/observe"
)

func TestCommandRequiresExplicitInputs(t *testing.T) {
	for _, args := range [][]string{nil, {"--config", "missing"}, {"--timeout", "1s"}, {"--config", "missing", "--timeout", "-1s"}, {"--config", "missing", "--timeout", "1s", "extra"}} {
		var output bytes.Buffer
		if run(context.Background(), args, &output, &output) == nil {
			t.Fatal("invalid command accepted", args)
		}
	}
	var help bytes.Buffer
	if run(context.Background(), []string{"--help"}, &help, &help) != nil || !strings.Contains(help.String(), "timeout") {
		t.Fatal("help failed")
	}
}

func TestCommandEmitsReportWithoutEndpointSecrets(t *testing.T) {
	config := observe.Config{ChainID: "32659", NetworkID: "32659", Genesis: common.HexToHash("0x1"), AnchorNumber: 1, AnchorHash: common.HexToHash("0x2"), Nodes: []observe.NodeConfig{{Name: "retired-backup", Role: "retired", Wallet: common.HexToAddress("0x1"), Endpoint: "https://user:secret@example.invalid/?token=hidden"}}}
	data, err := json.Marshal(config)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "config.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	var output, diagnostics bytes.Buffer
	if err := run(context.Background(), []string{"--config", path, "--timeout", "1s"}, &output, &diagnostics); err != nil {
		t.Fatal(err)
	}
	var report observe.Report
	if json.Unmarshal(output.Bytes(), &report) != nil || report.Version != 1 || report.Nodes[0].Consistency != "not_applicable" || report.Nodes[0].SavedIntent != "unknown" {
		t.Fatal(output.String())
	}
	if strings.Contains(output.String(), "secret") || strings.Contains(output.String(), "hidden") || diagnostics.Len() != 0 {
		t.Fatal("unexpected output")
	}
}
