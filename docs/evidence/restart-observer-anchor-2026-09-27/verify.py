import hashlib
import json
import re
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
windows_run = evidence / "attempt-3/windows"
linux_run = evidence / "attempt-4/linux"
services = linux_run / "services"
fixture = workspace / "docs/evidence/restart-observer-mining-2026-09-27/attempt-3/mining"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


for name, expected in read_json(evidence / "inputs.sha256.json").items():
    require(digest(workspace / name) == expected, f"Input changed: {name}")
first = evidence / "attempt-1/linux"
require((first / "service-exit.txt").read_text().strip() == "1", "Missing initial service failure")
require(read_json(first / "services/node-2-anchor-timeline.json")["Issue"] == "block 25: native logs outside a direct native call", "Initial observer limitation changed")
for platform in ["windows", "linux"]:
    failed = evidence / "attempt-2" / platform
    require((failed / "test-exit.txt").read_text().strip() == "1" and "expected recorded automatic maturity conversion" in (failed / "tests.txt").read_text(), "Missing fixture-selection failure")
third = evidence / "attempt-3/linux"
require((third / "service-exit.txt").read_text().strip() == "1" and "expected the inherited empty-owner RPC null result" in (third / "services-race.txt").read_text(), "Missing null-capture test failure")
sources = read_json(windows_run / "sources.json")
for name, expected in sources.items():
    require(digest(workspace / name) == expected, f"Source changed: {name}")
linux_sources = {}
for line in (linux_run / "sources.sha256").read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    linux_sources[name] = expected
require(sources == linux_sources, "Platform source manifests differ")
for line in (linux_run / "test-sources.sha256").read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    require(digest(workspace / name) == expected, f"Service test source changed: {name}")

tests = {}
for platform, folder in [("windows", windows_run), ("linux", linux_run)]:
    output = (folder / "tests.txt").read_text(encoding="utf-8")
    require((folder / "test-exit.txt").read_text().strip() == "0", f"{platform} exit failed")
    require("FAIL" not in output and "DATA RACE" not in output, f"{platform} suite failure")
    for package in ["internal/observe", "cmd/fsn-observe"]:
        require(re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/" + re.escape(package) + r"\s", output, re.M), f"Missing {platform} package")
    require((folder / "build.txt").read_bytes() == b"", f"{platform} build diagnostics")
    tests[platform] = {"passes_including_subtests": len(re.findall(r"^\s*--- PASS:", output, re.M)), "race_detection": platform == "linux", "log_sha256": digest(folder / "tests.txt")}
require(len({tests[p]["passes_including_subtests"] for p in tests}) == 1, "Platform counts differ")
require((linux_run / "build-tests.txt").read_bytes() == b"", "Service build diagnostics")
network = (linux_run / "network.txt").read_text().splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network interface")

exports = {}
for name in ["inventory.json", "timeline.json", "history.jsonl"]:
    windows, linux = windows_run / name, linux_run / name
    require(windows.read_bytes() == linux.read_bytes(), f"Platform export differs: {name}")
    exports[name] = digest(windows)
inventory = read_json(windows_run / "inventory.json")
timeline = read_json(windows_run / "timeline.json")
owner = inventory["Wallet"]
original_events = [json.loads(line) for line in (fixture / "cold-history-export.jsonl").read_text().splitlines()]
baseline = next(node["Tickets"] for node in original_events[1]["Report"]["Nodes"] if node["Wallet"] == owner)
ledger = {key: value for key, value in read_json(fixture / "ledger-29.json")["Tickets"].items() if value["Owner"] == owner}
require(inventory["Status"] == "ready" and inventory["Tickets"] == baseline, "Retained anchor inventory differs")
require(timeline["BaselineSequence"] == 11 and timeline["Status"] == "complete_for_retained_prefix" and timeline["Inventory"] == ledger and timeline["Through"]["Number"] == 29, "Retained final ledger differs")

require((linux_run / "service-exit.txt").read_text().strip() == "0", "Service exit failed")
service_log = (linux_run / "services-race.txt").read_text(encoding="utf-8")
require("--- PASS: TestObserverNodeServices" in service_log and "FAIL" not in service_log and "DATA RACE" not in service_log, "Service race test failed")
require(service_log.count("--- PASS: TestRestartNodeRehearsal") == 2, "Missing clean child exits")
truth = read_json(services / "prepared-truth.json")
anchor = read_json(services / "anchor-inventory-truth.json")
for i, node in enumerate(["node-1", "node-2"]):
    require(read_json(services / (node + "-before-anchor.json"))["Status"] == "missing_baseline", "Service baseline was preseeded")
    actual = read_json(services / (node + "-anchor-inventory.json"))
    require(actual["Status"] == "ready" and actual["Tickets"] == anchor["Tickets"], "Service anchor inventory differs")
    require(actual["Anchor"]["Hash"] == actual["AnchorAfter"]["Hash"] == anchor["Header"]["hash"], "Service anchor identity differs")
    derived = read_json(services / (node + "-anchor-timeline.json"))
    require(derived["Status"] == "complete_for_retained_prefix" and derived["Inventory"] == truth[i]["Tickets"] and derived["Through"]["Hash"] == truth[i]["Header"]["hash"], "Service current inventory differs")
reorg = read_json(services / "anchor-reorg-timeline.json")
require(reorg["Status"] == "complete_for_retained_prefix" and reorg["Inventory"] == truth[1]["Tickets"] and reorg["Through"]["Hash"] == truth[1]["Header"]["hash"], "Reorg inventory differs")
require(read_json(services / "empty-wallet-native-response.json") is None, "Missing actual empty RPC null")
empty = read_json(services / "empty-wallet-anchor.json")
require(empty["Status"] == "ready" and empty["Tickets"] == {}, "Empty RPC result not normalized")
captures = list(services.glob("*-state.json"))
require(len(captures) >= 27, "Missing service state captures")
for path in captures:
    state = read_json(path)
    require(state["Before"] == state["After"], f"Command changed state: {path.name}")
for path in services.glob("*-stderr.txt"):
    require(path.read_bytes() == b"", f"Service command diagnostics: {path.name}")
result = {"tests": tests, "exports": exports, "services": {"passed": True, "unchanged_state_captures": len(captures), "historical_transports": ["IPC", "HTTP"], "empty_rpc_null": True, "replacement_inventory_matches": True}, "limitations": ["controlled compact state only", "not proof of remote state", "no production historical-state or workload validation"]}
(evidence / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
