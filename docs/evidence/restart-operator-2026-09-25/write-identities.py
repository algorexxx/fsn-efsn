from pathlib import Path
import hashlib
import json
import subprocess

directory = Path(__file__).resolve().parent
workspace = directory.parents[2]


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        while data := source.read(1024 * 1024):
            checksum.update(data)
    return checksum.hexdigest()


for name in ["windows-unit.txt", "windows-integration.txt",
             "linux-unit-race.txt", "linux-integration-race.txt"]:
    lines = (directory / name).read_text(encoding="utf-8").splitlines()
    assert "PASS" in lines and not any("--- FAIL:" in line or "WARNING: DATA RACE" in line for line in lines), name

sources = ["cmd/fsn-recovery/main.go", "cmd/fsn-recovery/operator.go",
           "cmd/fsn-recovery/operator_test.go", "internal/recovery/approval.go",
           "internal/recovery/offline.go", "internal/recovery/signing.go",
           "internal/recovery/signing_test.go", "internal/recovery/keystore.go",
           "internal/recovery/keystore_test.go", "internal/recovery/operator.go",
           "tests/restart/recovery_operator_test.go"]
binaries = ["tmp/fsn-recovery-operator.exe", "tmp/fsn-recovery-operator-linux",
            "tmp/recovery-operator-windows-tests.exe", "tmp/recovery-operator-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "7c389ab"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1; Linux unit tests, command and integration binary with race detection; GOMAXPROCS=2; offline cached modules; Linux integration network isolated",
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "controlled_command_blocks_per_platform": 3,
    "scope": "Final unprefixed logs cover actual CLI review, full report rebuild, initialization, signing and export on sparse state with public encrypted scalars 1/2, credential and lock failures, pre-reservation process kill and approved/legacy interruption regressions. Initial logs predate report-rebuild and final input/lock checks. No real key, full-state fixture, W: data or replay checkpoint opened. No new dependencies. Not a reproducible release-build or power-loss attestation."
}
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.name}\n")
print(f"Recorded {len(sources)} source files, four binaries and checksums for {len(files)} evidence files")
