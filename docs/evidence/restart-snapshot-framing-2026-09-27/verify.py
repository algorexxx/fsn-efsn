import hashlib
import json
import re
import subprocess
from pathlib import Path


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = (evidence / "baseline.txt").read_text(encoding="utf-8").strip()
original = (evidence / "before-snapshot.go.txt").read_bytes().replace(b"\r\n", b"\n")
recorded = subprocess.run(["git", "show", f"{baseline}:consensus/datong/snapshot.go"], cwd=workspace, check=True, capture_output=True).stdout
require(original == recorded, "Original parser differs from baseline")
current = (workspace / "consensus/datong/snapshot.go").read_bytes().replace(b"\r\n", b"\n")
guard = b'\tif len(data) < 5 {\n\t\treturn errors.New("data length error")\n\t}\n'
require(current.count(guard) == 1 and current.replace(guard, b"", 1) == original, "Runtime diff exceeds the three-line guard")
before = (evidence / "before-windows.txt").read_text(encoding="utf-8")
failures = re.findall(r"--- FAIL: TestSnapshotRejectsTruncatedCount/(\S+)", before)
require(set(failures) == {f"length_{n}_spare_{spare}" for n in range(1, 5) for spare in [0, 65]}, "Missing original truncated-count failures")
require(before.count("truncated count panicked instead of returning an error") == 8, "Missing recovered panics")
require("--- PASS: TestSnapshotPreservesValidEncoding" in before and "--- PASS: TestSnapshotRejectsInvalidFraming" in before, "Original controls did not pass")
require((evidence / "before-exit.txt").read_text(encoding="utf-8").strip() == "1", "Original test unexpectedly succeeded")

inputs = json.loads((evidence / "after-windows/inputs.sha256.json").read_text(encoding="utf-8"))
for path, expected in inputs.items():
    require(digest(workspace / path) == expected, f"Windows input changed: {path}")
linux_inputs = {}
for line in (evidence / "after-linux/sources.sha256").read_text(encoding="utf-8").splitlines():
    expected, path = line.split(maxsplit=1)
    require(digest(workspace / path) == expected, f"Linux input changed: {path}")
    linux_inputs[path] = expected
require(inputs == linux_inputs, "Platform source/input identities differ")

passed = {}
for name in ["after-windows/parser.txt", "after-linux/parser-race.txt", "after-linux/compatibility-race.txt"]:
    log = (evidence / name).read_text(encoding="utf-8")
    require("FAIL" not in log and "DATA RACE" not in log and re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/", log, re.M), f"Missing passing result: {name}")
    passed[name] = {"passes_including_subtests_and_child_output": len(re.findall(r"^\s*--- PASS:", log, re.M)), "sha256": digest(evidence / name)}
compatibility = (evidence / "after-linux/compatibility-race.txt").read_text(encoding="utf-8")
for name in ["TestHeaderBatchUsesUnstoredParents", "TestFinalizeParentIsolatedFromConcurrentImport", "TestColdHeaderValidationBoundaries"]:
    require(f"--- PASS: {name} (" in compatibility, f"Missing compatibility test: {name}")
for mode in ["headers_only", "headers_receipts", "headers_bodies", "headers_complete", "headers_missing_receipt", "headers_incremental", "invalid_header", "full_import"]:
    require(f"--- PASS: TestColdHeaderValidationBoundaries/{mode} " in compatibility, f"Missing cold case: {mode}")
windows_setup = (evidence / "after-windows/compatibility.txt").read_text(encoding="utf-8")
require("module lookup disabled by GOPROXY=off" in windows_setup and "[setup failed]" in windows_setup, "Windows compatibility limitation changed")
require((evidence / "after-windows/exit.txt").read_text(encoding="utf-8").strip() == "1", "Windows compatibility failure not recorded")
require((evidence / "after-linux/exit.txt").read_text(encoding="utf-8").strip() == "0", "Linux runner failed")
fuzz = (evidence / "after-linux/fuzz-race.txt").read_text(encoding="utf-8")
require("PASS" in fuzz and "FAIL" not in fuzz and "DATA RACE" not in fuzz, "Fuzz run failed")
executions = [int(value) for value in re.findall(r"execs: (\d+)", fuzz)]
require(executions and max(executions) > 0, "Missing fuzz executions")
network = (evidence / "after-linux/network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network surface")
require(not (workspace / "tests/restart/snapshot_framing_test.go").exists(), "Unexecuted signed-header draft remains")

checks = {
    "baseline": baseline,
    "runtime_change": "Three-line minimum-size guard in snapshot.SetBytes; original decoder otherwise byte-identical after newline normalization.",
    "original_local_panic_cases": len(failures),
    "shared_inputs_verified": len(inputs),
    "passing_logs": passed,
    "windows_header_compatibility": "not run: offline dependency cache incomplete; setup failure retained",
    "linux_race_checks": "parser, existing header/import compatibility and bounded in-memory fuzz passed",
    "fuzz_executions": max(executions),
    "fuzz_requested_seconds": 10,
    "limitations": ["No signed malformed-header, process-crash or peer-network test was run.", "Local parser behavior is reproduced; remote exploitability and process-level impact remain unverified.", "P16 is a candidate requiring independent release review."],
}
(evidence / "checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
