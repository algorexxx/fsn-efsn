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


for name in ["windows-unit-final.txt", "windows-integration-final.txt",
             "linux-unit-final-race.txt", "linux-integration-race.txt"]:
    lines = (directory / name).read_text(encoding="utf-8").splitlines()
    assert "PASS" in lines and not any("--- FAIL:" in line or "WARNING: DATA RACE" in line for line in lines), name

sources = ["internal/recovery/offline.go", "internal/recovery/offline_test.go",
           "tests/restart/recovery_offline_test.go"]
extra = ["tests/restart/snapshot_indexes_test.go", "tests/restart/snapshot_package_test.go",
         "tests/restart/snapshot_service_test.go"]
binaries = ["tmp/recovery-offline-windows-tests.exe", "tmp/recovery-offline-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "0ad0136"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection; GOMAXPROCS=2; offline cached modules",
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "additional_snapshot_test_source_sha256": {name: digest(workspace / name) for name in extra},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "scope": "Only small synthetic offline-signing, export, guard and handover tests ran. The restart binaries also include the listed earlier uncommitted snapshot tests; they were not selected. No real key, full-state fixture or W: data was opened. This is not a reproducible release-build attestation."
}
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.name}\n")
print(f"Recorded identities and checksums for {len(files)} evidence files")
