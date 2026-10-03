import hashlib
import json
import statistics
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
linux = evidence / "attempt-1" / "linux"
windows = evidence / "attempt-1" / "windows"


def require(condition, message):
    if not condition:
        raise ValueError(message)


linux_sources = {}
for line in (linux / "sources.sha256").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(maxsplit=1)
    linux_sources[name] = digest
windows_sources = {name.replace("\\", "/"): digest for name, digest in json.loads((windows / "sources.json").read_text(encoding="utf-8")).items()}
require(linux_sources == windows_sources, "Platforms tested different source")
for name, digest in linux_sources.items():
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest, f"Source changed: {name}")
for line in (linux / "fixture.sha256").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(maxsplit=1)
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest, f"Fixture changed: {name}")
for folder, exit_file, log_file in [(linux, "tests-exit.txt", "tests-race.txt"), (windows, "test-exit.txt", "tests.txt"), (linux, "cost-exit.txt", "cost-test.txt")]:
    require((folder / exit_file).read_text(encoding="utf-8").strip() == "0", f"Failed run: {folder}/{exit_file}")
    log = (folder / log_file).read_text(encoding="utf-8")
    require("PASS" in log and "FAIL" not in log and "DATA RACE" not in log, f"Unclean run: {log_file}")
for folder, name in [(windows, "tests.txt"), (linux, "tests-race.txt")]:
    log = (folder / name).read_text(encoding="utf-8")
    require("--- PASS: TestBackfillRetainedForkAndResume" in log and "--- PASS: TestCommandHistoryLifecycle" in log, "Missing regression results")
require((linux / "build.txt").read_bytes() == b"", "Build diagnostics")
network = (linux / "network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected interface")
require("canonical-change details: got" in (evidence / "initial-format-failure.txt").read_text(encoding="utf-8"), "Missing original formatting failure")
samples = json.loads((linux / "cost.json").read_text(encoding="utf-8"))
require([sample["PriorReports"] for sample in samples] == [10, 100, 1000], "Unexpected workload sizes")
summary = []
for sample in samples:
    require(sample["FinalReports"] == sample["PriorReports"] + 1 and 0 < sample["LogicalBytes"] < 64 * 1024 * 1024 and sample["ClosedFileBytes"] > 0, "Invalid retained history size")
    operations = {}
    for name, count in [("status", 3), ("append", 1), ("export_discard", 3), ("reopen_status", 3)]:
        matches = [item for item in sample["Operations"] if item["Name"] == name]
        require(len(matches) == count and all(item["Nanoseconds"] > 0 and item["AllocatedBytes"] > 0 for item in matches), f"Missing measurements: {name}")
        times = [item["Nanoseconds"] / 1e6 for item in matches]
        operations[name] = {"samples": count, "median_ms": statistics.median(times), "min_ms": min(times), "max_ms": max(times), "median_allocated_bytes": statistics.median(item["AllocatedBytes"] for item in matches)}
    summary.append({"prior_reports": sample["PriorReports"], "final_reports": sample["FinalReports"], "logical_bytes": sample["LogicalBytes"], "closed_file_bytes": sample["ClosedFileBytes"], "operations": operations})
bytes_per_report = (samples[-1]["LogicalBytes"] - samples[-2]["LogicalBytes"]) / (samples[-1]["FinalReports"] - samples[-2]["FinalReports"])
result = {"passed": True, "windows_suites": True, "linux_race_suites": True, "non_race_cost_run": True, "samples": summary, "logical_growth_bytes_per_report": bytes_per_report, "illustrative_snapshot_only_64_mib_hours": {str(seconds): 64 * 1024 * 1024 / bytes_per_report * seconds / 3600 for seconds in [15, 60]}, "limitations": ["one repeated retained two-node snapshot with retimed observations", "no RPC acquisition, growing block ancestry, or timeline cost", "same-process reopen with OS caches warm, not cold storage", "allocation totals are not retained RAM or peak RSS", "physical sizes benefit from repeated-content compression", "cadence and capacity arithmetic are estimates, not deployment guarantees"]}
(evidence / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
