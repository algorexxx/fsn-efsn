import hashlib
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
inputs = json.loads((evidence / "inputs.sha256.json").read_text(encoding="utf-8"))
changed = [name for name, expected in inputs.items()
           if hashlib.sha256((workspace / name).read_bytes()).hexdigest() != expected]
assert not changed, changed

results = {}
for name in ("windows.txt", "linux-race.txt"):
    log = (evidence / name).read_text(encoding="utf-8")
    assert "FAIL" not in log and "WARNING: DATA RACE" not in log, name
    assert log.count("\nPASS\n") == 2, name
    assert "github.com/FusionFoundation/efsn/v5/internal/observe" in log, name
    assert "github.com/FusionFoundation/efsn/v5/cmd/fsn-observe" in log, name
    results[name] = {"passed": True, "test_and_subtest_pass_lines": log.count("--- PASS:")}

reports = sorted((evidence / "reports").glob("*.json"))
assert reports
for path in reports:
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["Version"] == 1, path
    assert all(node["SavedIntent"] == "unknown" for node in report["Nodes"]), path
    assert all("Endpoint" not in node for node in report["Nodes"]), path

binaries = {}
for name in ("fsn-observe.exe", "fsn-observe-linux"):
    path = workspace / "tmp/restart-observer" / name
    binaries[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}

summary = {
    "scope": "local retained-data RPC adapters; no chain database, new miner run or alert delivery",
    "source_and_retained_input_files_unchanged": len(inputs),
    "test_results": results,
    "reports": len(reports),
    "binaries": binaries,
    "node_runtime_changes": False,
}
(evidence / "checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
