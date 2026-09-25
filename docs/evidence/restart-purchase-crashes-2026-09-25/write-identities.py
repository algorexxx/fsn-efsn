from pathlib import Path
import hashlib
import json
import re
import subprocess

directory = Path(__file__).resolve().parent
workspace = directory.parents[2]


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        while data := source.read(1024 * 1024):
            checksum.update(data)
    return checksum.hexdigest()


expected = {f"new/{pool}/{cut}/{phase}" for pool in ["restore", "lost"]
            for cut in ["save", "submit"] for phase in ["before", "after"]}
expected |= {f"confirmed/restore/{cut}/{phase}" for cut in ["save", "retire"]
             for phase in ["before", "after"]}
expected |= {f"{scenario}/restore/{cut}/{phase}"
             for scenario, cut in [("replaced", "retire"), ("adopt", "save")]
             for phase in ["before", "after"]}
durations = {}
for name in ["windows-crashes.txt", "linux-crashes-race.txt"]:
    data = (directory / name).read_text(encoding="utf-8")
    assert "PASS" in data.splitlines(), name
    assert not any(marker in data for marker in ["--- FAIL:", "--- SKIP:", "WARNING: DATA RACE"]), name
    cases = re.findall(r"^    --- PASS: TestAutomaticPurchaseCrashBoundaries/(\S+) \(", data, re.MULTILINE)
    assert len(cases) == 16 and set(cases) == expected, (name, cases)
    durations[name] = float(re.search(r"^--- PASS: TestAutomaticPurchaseCrashBoundaries \(([0-9.]+)s\)", data, re.MULTILINE).group(1))

subprocess.run(["git", "diff", "--exit-code", "33e80d1", "--", ".", ":!docs/**", ":!tests/**"], cwd=workspace, check=True, stdout=subprocess.PIPE)
sources = ["tests/restart/purchase_crash_test.go", "tests/restart/purchase_crash_recovery_test.go"]
binaries = ["tmp/purchase-crash-windows-tests.exe", "tmp/purchase-crash-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "33e80d1"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection; GOMAXPROCS=2; offline modules; Linux parent and children network isolated",
    "production_source_changes": False,
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "final_seconds": durations,
    "abrupt_exits_per_platform": len(expected),
    "child_processes_per_platform": 4 * len(expected),
    "final_cases": sorted(expected),
    "scope": "Before/after automatic purchase save, pool submission, retirement and pool adoption; exact record/pool checks, canonical nonce/receipt/ticket evidence, initially locked recovery, one retry interval without additional submission and independent cold reopening. Sparse state and public key 1; perpetual other-owner ticket intervals are synthetic scaffolding. Initial logs predate strengthened assertions. No real key, full-state data or production code changes; not power-loss, cuts within storage writes, full node/peer reorganization or exactly-once delivery evidence."
}
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.relative_to(directory).as_posix()}\n")
print(f"PASS: {len(files)} evidence files; sixteen final cuts per platform; production code unchanged")
