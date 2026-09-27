import hashlib
import json
import re
from pathlib import Path


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-1"
services = attempt / "services"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


inputs = read_json(evidence / "inputs.sha256.json")
for path, expected in inputs.items():
    require(digest(workspace / path) == expected, f"Input changed: {path}")
for line in (attempt / "sources.sha256").read_text(encoding="utf-8").splitlines():
    expected, path = line.split(maxsplit=1)
    require(digest(workspace / path) == expected, f"Linux source changed: {path}")

tests = {}
for platform, log in [("windows", evidence / "windows.txt"), ("linux", attempt / "linux-race.txt")]:
    output = log.read_text(encoding="utf-8")
    require("FAIL" not in output and "DATA RACE" not in output, f"Failed {platform} tests")
    for package in ["internal/observe", "cmd/fsn-observe"]:
        require(re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/" + re.escape(package) + r"\s", output, re.M), f"Missing {platform} package: {package}")
    tests[platform] = {"passes_including_subtests": len(re.findall(r"^\s*--- PASS:", output, re.M)), "race_detection": platform == "linux", "log_sha256": digest(log)}
for log in [evidence / "windows-build.txt", attempt / "build-tests.txt", attempt / "build-observer.txt"]:
    require(log.read_bytes() == b"", f"Unexpected compiler output: {log.name}")

exports = {}
for name in ["fork-history.jsonl", "fork-status.json"]:
    windows, linux = evidence / "windows-history" / name, attempt / "linux-history" / name
    require(windows.read_bytes() == linux.read_bytes(), f"Platform export mismatch: {name}")
    exports[name] = digest(windows)
fixture_status = read_json(evidence / "windows-history/fork-status.json")
require(fixture_status["Sequence"] == 5 and fixture_status["Blocks"][0]["StoredThrough"]["Number"] == 25, "Unexpected fixture final state")
changes = [item for item in fixture_status["Incidents"] if item["Kind"] == "canonical_history_change"]
require(len(changes) == 1 and changes[0]["Status"] == "open" and changes[0]["Occurrences"] == 2 and changes[0]["LastReviewSequence"] == 4, "Fork did not reopen the reviewed incident")

require((attempt / "exit.txt").read_text(encoding="utf-8").strip() == "0", "Service test exit failed")
service_log = (attempt / "services-race.txt").read_text(encoding="utf-8")
require("--- PASS: TestObserverNodeServices" in service_log and "FAIL" not in service_log and "DATA RACE" not in service_log, "Service race test failed")
require(service_log.count("--- PASS: TestRestartNodeRehearsal") == 2, "Missing clean child node exits")
network = (attempt / "network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network surface")
node_states = sorted(services.glob("*-state.json"))
require(len(node_states) == 18, "Missing command state captures")
for path in node_states:
    state = read_json(path)
    require(state["Before"] == state["After"], f"Observer changed node state: {path.name}")

initial = read_json(services / "ipc-divergence.json")
truth = read_json(services / "prepared-truth.json")
local_hash = truth[0]["Header"]["hash"]
remote_hash = initial["Comparison"]["Hashes"][1]
final_hash = truth[1]["Header"]["hash"]
expected_backfills = [
    ("backfill-local", "node-1", 2, 25, local_hash, "complete_at_observation"),
    ("backfill-http-partial", "node-2", 3, 25, remote_hash, "batch_limit"),
    ("backfill-http-complete", "node-2", 4, 26, final_hash, "complete_at_observation"),
    ("backfill-reorg-partial", "node-1", 6, 25, remote_hash, "batch_limit"),
    ("backfill-reorg-complete", "node-1", 7, 26, final_hash, "complete_at_observation"),
    ("backfill-endpoint-lost", "node-2", 8, 26, final_hash, "unavailable"),
]
for name, node, sequence, number, block_hash, outcome in expected_backfills:
    status = read_json(services / (name + ".json"))
    coverage = [entry for entry in status["Blocks"] if entry["Node"] == node]
    require(status["Sequence"] == sequence and len(coverage) == 1, f"Missing backfill: {name}")
    require(coverage[0]["StoredThrough"] == {"Number": number, "Hash": block_hash} and coverage[0]["Status"] == outcome, f"Wrong backfill result: {name}")
    require((services / (name + "-stderr.txt")).read_bytes() == b"", f"Unexpected backfill stderr: {name}")
complete = read_json(services / "backfill-reorg-complete.json")
require({item["Kind"] for item in complete["Incidents"] if item["Node"] == "node-1" and item["Status"] == "open"} >= {"canonical_history_change", "block_coverage", "receipt_change"}, "Completion automatically closed a review")
require(complete["Blocks"][1]["Status"] == "not_rechecked", "Snapshot silently refreshed other node block coverage")

export_text = (services / "history-export.json").read_text(encoding="utf-8")
records = [json.loads(line) for line in export_text.splitlines()]
require(len(records) == 8 and "Metadata" in records[0] and [record["Sequence"] for record in records[1:]] == list(range(1, 8)), "Service export sequence changed")
require(sum("Backfill" in record for record in records[1:]) == 5, "Missing persisted backfills")
for name in ["local-25", "remote-25", "remote-26"]:
    require("0x" + (services / (name + ".rlp")).read_bytes().hex() in export_text, f"Lost displaced/original block: {name}")
require('"Endpoint"' not in export_text, "Endpoint configuration persisted in history")

binaries = {}
for line in (attempt / "binaries.sha256").read_text(encoding="utf-8").splitlines():
    expected, path = line.split(maxsplit=1)
    if (workspace / path).exists():
        require(digest(workspace / path) == expected, f"Binary changed: {path}")
        binaries[path] = expected
windows_binary = workspace / "tmp/restart-observer-backfill/fsn-observe.exe"
if windows_binary.exists():
    binaries[windows_binary.relative_to(workspace).as_posix()] = digest(windows_binary)

checks = {
    "baseline": "4edd015",
    "inputs_verified": len(inputs),
    "tests": tests,
    "identical_fixture_exports": exports,
    "service_test": "passed with race detection; loopback only",
    "service_log_sha256": digest(attempt / "services-race.txt"),
    "commands_preserving_node_state": len(node_states),
    "service_backfill_results_verified": len(expected_backfills),
    "service_export_events": len(records) - 1,
    "both_branches_retained": True,
    "built_binaries_present": binaries,
    "limitations": ["No ordinary live mining or production workload.", "RPC commitments and continuity, not state execution or consensus/finality validation.", "Native purchase/selection/retreat accounting and notification delivery remain separate."],
}
(evidence / "checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
