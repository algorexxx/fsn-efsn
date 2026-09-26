import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = (workspace / "tests/restart/network_partition_linux_test.go").read_text(encoding="utf-8")
source = source.replace('"github.com/FusionFoundation/efsn/v5/p2p"', '"github.com/FusionFoundation/efsn/v5/log"\n\t"github.com/FusionFoundation/efsn/v5/p2p"', 1)
source = source.replace('t.Run("short_loss_retains_tcp_connection",', 'log.Root().SetHandler(log.StreamHandler(os.Stderr, log.TerminalFormat(false)))\n\tt.Run("short_loss_retains_tcp_connection",', 1)
(evidence / "trace-fixture.go.txt").write_text(source, encoding="utf-8", newline="\n")
linux = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
mapping = {"Replace": {linux + "tests/restart/network_partition_linux_test.go": linux + "docs/evidence/restart-network-partitions-2026-09-25/trace-fixture.go.txt"}}
(evidence / "trace-overlay.json").write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8", newline="\n")
