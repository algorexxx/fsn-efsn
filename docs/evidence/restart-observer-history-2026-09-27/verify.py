import hashlib
import json
import re
from pathlib import Path


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


inputs = json.loads((evidence / "inputs.sha256.json").read_text(encoding="utf-8"))
for relative, expected in inputs.items():
    require(digest(workspace / relative) == expected, f"Input changed: {relative}")

packages = ["internal/observe", "cmd/fsn-observe"]
tests = {}
for platform, filename in [("windows", "windows.txt"), ("linux", "linux-race.txt")]:
    output = (evidence / filename).read_text(encoding="utf-8")
    require("FAIL" not in output and "DATA RACE" not in output, f"Failed {platform} tests")
    for package in packages:
        require(
            re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/" + re.escape(package) + r"\s", output, re.M),
            f"Missing {platform} package completion: {package}",
        )
    require((evidence / f"{platform}-build.txt").read_bytes() == b"", f"Unexpected {platform} compiler output")
    tests[platform] = {
        "packages_passed": packages,
        "test_and_subtest_passes": len(re.findall(r"^\s*--- PASS:", output, re.M)),
        "race_detection": platform == "linux",
        "log_sha256": digest(evidence / filename),
    }

exports = {}
for filename in ["timeline.jsonl", "timeline-status.json"]:
    windows = evidence / "windows-history" / filename
    linux = evidence / "linux-history" / filename
    require(windows.read_bytes() == linux.read_bytes(), f"Platform export mismatch: {filename}")
    exports[filename] = digest(windows)

records = [json.loads(line) for line in (evidence / "windows-history/timeline.jsonl").read_text(encoding="utf-8").splitlines()]
require(len(records) == 10 and "Metadata" in records[0], "Expected metadata plus nine events")
events = records[1:]
require([event["Sequence"] for event in events] == list(range(1, 10)), "Event sequence changed")
require(sum("Report" in event for event in events) == 7, "Expected seven retained reports")
reviews = [(event["Sequence"], event["Review"]["Action"]) for event in events if "Review" in event]
require(reviews == [(3, "acknowledge"), (6, "resolve")], "Review sequence changed")

status = json.loads((evidence / "windows-history/timeline-status.json").read_text(encoding="utf-8"))
require(status["Sequence"] == 9 and status["Coverage"] == "snapshots_only_no_block_backfill", "Unexpected final status")
purchase = "0x3ff9d9b3581102af0335f8ba36d99e404fff66209a9715074fa941ac268546c7"
receipt = [incident for incident in status["Incidents"] if incident["Node"] == "node-1" and incident["Kind"] == "receipt_change" and incident["Transaction"] == purchase]
require(len(receipt) == 1, "Expected one stable purchase receipt incident")
receipt = receipt[0]
for key, expected in {"Status": "open", "Observation": "unknown", "Occurrences": 2, "FirstSequence": 4, "LastSequence": 8, "LastReviewSequence": 6}.items():
    require(receipt[key] == expected, f"Unexpected receipt incident {key}")
require(events[5]["Review"] == receipt["LastReview"], "Previous review not retained")
require(receipt["LastReview"]["Incident"] == receipt["ID"], "Incident identity changed")

network = (evidence / "linux-network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Expected isolated loopback only")
binaries = {}
for filename in ["fsn-observe.exe", "fsn-observe-linux"]:
    binary = workspace / "tmp/restart-observer-history" / filename
    if binary.exists():
        binaries[filename] = {"sha256": digest(binary), "bytes": binary.stat().st_size}
        if filename == "fsn-observe-linux":
            expected = (evidence / "linux-binary.sha256").read_text(encoding="utf-8").split()[0]
            require(binaries[filename]["sha256"] == expected, "Linux binary changed")

checks = {
    "baseline": "b13c92c",
    "inputs_verified": len(inputs),
    "tests": tests,
    "exports_identical": exports,
    "events": len(events),
    "reports": 7,
    "reviews": reviews,
    "reopened_receipt_incident": receipt["ID"],
    "linux_network": "loopback_only",
    "binaries_present": binaries,
    "limitations": [
        "Retained actual-service reports with synthetic times and recurrence variants; no new live node services.",
        "Abrupt process exit after a synchronous write, not power loss or interrupted-write fault injection.",
        "Snapshot history only; complete block coverage and production storage/load remain unvalidated.",
    ],
}
(evidence / "checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
