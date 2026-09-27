import hashlib
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-4"
services = attempt / "services"
assert (attempt / "exit.txt").read_text(encoding="utf-8").strip() == "0"
log = (attempt / "services-race.txt").read_text(encoding="utf-8")
assert "--- PASS: TestObserverNodeServices" in log
assert log.count("--- PASS: TestRestartNodeRehearsal") == 2
assert "FAIL" not in log and "WARNING: DATA RACE" not in log
for line in (attempt / "sources.sha256").read_text(encoding="utf-8").splitlines():
    expected, name = line.split("  ", 1)
    assert hashlib.sha256((workspace / name).read_bytes()).hexdigest() == expected, name

names = ["ipc-divergence", "http-divergence", "ipc-converged", "ipc-queued-gap",
         "ipc-disabled-producer", "ipc-wrong-identity", "ipc-endpoint-lost", "ipc-retired"]
summaries = {}
for name in names:
    assert (services / (name + "-stderr.txt")).read_bytes() == b"", name
    state = json.loads((services / (name + "-state.json")).read_text(encoding="utf-8"))
    assert state["Before"] == state["After"], name
    report = json.loads((services / (name + ".json")).read_text(encoding="utf-8"))
    assert report["Version"] == 1 and len(report["Nodes"]) == 2, name
    assert all(node["SavedIntent"] == "unknown" for node in report["Nodes"]), name
    summaries[name] = {
        "comparison": report["Comparison"]["Status"],
        "height": report["Comparison"]["Height"],
        "before_after_node_state_equal": True,
    }

result = json.loads((services / "result.json").read_text(encoding="utf-8"))
assert result["Passed"] and result["Samples"] == len(names)
assert not result["ObserverMutations"] and not result["LargeBackupRead"]
cleanup = json.loads((attempt / "cleanup.json").read_text(encoding="utf-8"))
assert cleanup["TemporaryNodeDirectoriesRemoved"] and not cleanup["ResidualProcesses"]
checks = {"passed": True, "runtime_source_changes": False, "observations": summaries,
          "cleanup": cleanup, "limits": "synthetic devnet services; controlled sync; no ordinary mining or notifications"}
(evidence / "checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
