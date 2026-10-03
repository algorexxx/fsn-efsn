import hashlib
import json
import statistics
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest(path):
    return {name: digest for digest, name in (line.split(maxsplit=1) for line in path.read_text(encoding="utf-8").splitlines())}


def clean_run(folder, exit_file, log_file):
    require((folder / exit_file).read_text(encoding="utf-8").strip() == "0", f"Failed run: {folder}")
    log = (folder / log_file).read_text(encoding="utf-8")
    require("PASS" in log and "FAIL" not in log and "DATA RACE" not in log, f"Unclean run: {folder}")
    return log


baseline = manifest(evidence / "baseline/sources.sha256")
candidate = manifest(evidence / "candidate/sources.sha256")
require(set(candidate) - set(baseline) == {"internal/observe/history_open_test.go"} and not set(baseline) - set(candidate), "Unexpected source set changes")
require([name for name in baseline if baseline[name] != candidate[name]] == ["internal/observe/history.go"], "Unexpected changed source")
for name, digest in candidate.items():
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest, f"Source changed: {name}")
measurements = {}
for variant, sources in [("baseline", baseline), ("candidate", candidate)]:
    root = evidence / variant
    clean_run(root, "test-exit.txt", "cost-test.txt")
    require((root / "build.txt").read_bytes() == b"", "Benchmark build diagnostics")
    for name in ["history.go", "history_cost_test.go"]:
        require(hashlib.sha256((root / (name + ".txt")).read_bytes()).hexdigest() == sources[f"internal/observe/{name}"], "Archived source mismatch")
    network = (root / "network.txt").read_text(encoding="utf-8").splitlines()
    require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected benchmark interface")
    measurements[variant] = read(root / "cost.json")
comparisons = []
for old, new in zip(measurements["baseline"], measurements["candidate"]):
    require(old["PriorReports"] == new["PriorReports"] and old["FinalReports"] == new["FinalReports"] and old["LogicalBytes"] == new["LogicalBytes"], "Benchmark data sizes differ")
    row = {"prior_reports": old["PriorReports"], "logical_bytes": old["LogicalBytes"]}
    for variant, sample in [("baseline", old), ("candidate", new)]:
        values = [item for item in sample["Operations"] if item["Name"] == "reopen_status"]
        require(len(values) == 3, "Missing benchmark samples")
        row[variant] = {"median_ms": statistics.median(item["Nanoseconds"] / 1e6 for item in values), "median_allocated_bytes": statistics.median(item["AllocatedBytes"] for item in values)}
    row["median_time_reduction_percent"] = 100 * (1 - row["candidate"]["median_ms"] / row["baseline"]["median_ms"])
    comparisons.append(row)
require([row["prior_reports"] for row in comparisons] == [10, 100, 1000], "Unexpected comparison sizes")
comparison = evidence / "attempt-2/comparison"
for variant in ["baseline", "candidate"]:
    clean_run(comparison / variant, "test-exit.txt", "tests.txt")
    require((comparison / variant / "build.txt").read_bytes() == b"", "Comparison build diagnostics")
    require(manifest(comparison / variant / "effective-sources.sha256") == (baseline if variant == "baseline" else candidate), "Wrong comparison source manifest")
overlay = read(comparison / "baseline/overlay.json")["Replace"]
require(len(overlay) == 2 and any(name.endswith("/history_open_test.go") and target == "" for name, target in overlay.items()) and any(name.endswith("/history.go") and target.endswith("/baseline/history.go.txt") for name, target in overlay.items()), "Unexpected baseline overlay")
outputs = {}
for name in ["timeline-status.json", "timeline.jsonl", "fork-status.json", "fork-history.jsonl", "node-1.json", "node-2.json"]:
    original = (comparison / "baseline" / name).read_bytes()
    require(original == (comparison / "candidate" / name).read_bytes(), f"Observable output differs: {name}")
    outputs[name] = hashlib.sha256(original).hexdigest()
require((evidence / "baseline/equivalence/test-exit.txt").read_text(encoding="utf-8").strip() == "127" and "No such file or directory" in (evidence / "baseline/equivalence/tests.txt").read_text(encoding="utf-8"), "Missing retained comparison-launch failure")
windows = evidence / "attempt-1/windows"
linux = evidence / "attempt-1/linux"
windows_sources = {name.replace("\\", "/"): digest for name, digest in read(windows / "sources.json").items()}
require(windows_sources == candidate, "Windows candidate source differs")
for name, digest in manifest(linux / "sources.sha256").items():
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest, f"Linux source changed: {name}")
tests = ["TestHistoryFirstOperationRejectionPreservesEvidence", "TestHistoryOpenedStatusDoesNotAliasLaterReads", "TestHistoryClosedBeforeFirstOperationRejectsAccess", "TestHistoryConcurrentFirstReviewsKeepSequenceGuard", "TestHistoryFirstWriteFailureDoesNotRetainUncommittedState", "TestHistoryCorruptionFailsClosed"]
for folder, log_file in [(windows, "tests.txt"), (linux, "tests-race.txt")]:
    log = clean_run(folder, "test-exit.txt", log_file)
    require(all(f"--- PASS: {name}" in log for name in tests), "Missing opening-state regression")
log = clean_run(linux, "workload-exit.txt", "workload-race.txt")
require("--- PASS: TestObserverMixedWorkloadBudget" in log and log.count("--- PASS: TestRestartNodeRehearsal") == 2, "Mixed workload or child exits missing")
require(all((linux / name).read_bytes() == b"" for name in ["build-tests.txt", "build-observer.txt"]), "Service build diagnostics")
root = linux / "workload"
result = read(root / "result.json")
require(result["Passed"] and result["OrdinaryMining"] and not result["LargeBackupRead"] and result["BudgetBytes"] == 524288, "Unexpected mixed workload result")
anchor, settled, before, final = [(root / name).read_bytes() for name in ["anchor-export.json", "settled-export.json", "before-retry-export.json", "offline-export.json"]]
require(settled.startswith(anchor) and final.startswith(settled) and final == before, "Mixed history changed or lost its prefix")
require(read(root / "offline-status.json") == read(root / "backfill-rejected-status.json"), "Rejected write changed offline status")
config, ledger = read(root / "ipc-config.json"), read(root / "final-ledger.json")
for node in config["Nodes"]:
    timeline = read(root / (node["Name"] + "-offline-timeline.json"))
    expected = {key: value for key, value in ledger["Tickets"].items() if value["Owner"] == node["Wallet"]}
    require(timeline["Status"] == "complete_for_retained_prefix" and timeline["Inventory"] == expected and timeline["Through"]["Hash"] == result["Final"]["hash"], "Offline inventory differs")
commands = read(root / "commands.json")
rejected = []
for command in commands:
    name = command["Name"]
    diagnostics = (root / (name + "-stderr.txt")).read_text(encoding="utf-8")
    if command["ExitCode"] == 1:
        require((root / (name + ".json")).read_bytes() == b"" and diagnostics == "history byte budget exhausted; evidence retained without pruning\n", "Unexpected command failure")
        rejected.append(name)
    else:
        require(command["ExitCode"] == 0 and diagnostics == "", "Unexpected command diagnostics")
require("retry-snapshot" in rejected and "retry-backfill" in rejected, "Missing retry rejection")
summary = {"passed": True, "comparison": comparisons, "byte_identical_outputs": outputs, "windows_suites": True, "linux_race_suites": True, "mixed_workload_race": {"passed": True, "final_height": int(result["Final"]["number"], 16), "logical_bytes": result["LogicalBytes"], "budget_bytes": result["BudgetBytes"], "rejected_commands": rejected, "offline_inventories_match": True, "exports_preserved": True}, "limitations": ["warm-cache same-process benchmark; not total deployed command latency", "first operation only; subsequent operations still replay", "no reduction in retained logical bytes or storage-budget requirement", "long advancing ancestry, retention and notification delivery remain open"]}
(evidence / "checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
