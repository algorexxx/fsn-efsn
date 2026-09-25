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


for name in ["windows-unit-final.txt", "windows-integration.txt",
             "linux-unit-final-race.txt", "linux-integration-race.txt"]:
    lines = (directory / name).read_text(encoding="utf-8").splitlines()
    assert "PASS" in lines and not any("--- FAIL:" in line or "WARNING: DATA RACE" in line for line in lines), name

sources = ["internal/recovery/approval.go", "internal/recovery/policy.go",
           "internal/recovery/policy_test.go", "internal/recovery/signing.go",
           "internal/recovery/offline.go", "tests/restart/recovery_approval_test.go",
           "tests/restart/recovery_offline_test.go"]
binaries = ["tmp/signing-approval-windows-tests.exe", "tmp/signing-approval-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "cedde9f"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection; GOMAXPROCS=2; offline cached modules; Linux integration network isolated",
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "approved_completed_cuts_per_platform": 9,
    "approved_uncertain_cuts_per_platform": 2,
    "scope": "Small-state approved and legacy offline signing tests with public scalars 1 and 2 only. Policy and exact-input checks run before reservation/signing; no real-key adapter, CLI signing command, complete-state fixture or W: data opened. Final unit logs include the added unfinished-donation advancement test; production and integration sources were unchanged after binary builds. This is not a reproducible release-build attestation."
}
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.name}\n")
print(f"Recorded source/binary identities and checksums for {len(files)} evidence files")
