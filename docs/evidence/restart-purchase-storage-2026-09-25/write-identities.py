import hashlib
import json
from pathlib import Path
import re
import subprocess


results = Path(__file__).resolve().parent
workspace = results.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=workspace, stderr=subprocess.PIPE).decode().strip()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


storage_cases = ["put_before", "put_after", "adopt_before", "adopt_after", "delete_before", "delete_after", "has", "get"]
peer_cases = ["purchase_peer_reinclusion", "purchase_peer_replacement"]
durations = {}
for filename, test, cases in [
    ("windows-storage.txt", "TestAutomaticPurchaseStorageErrors", storage_cases),
    ("linux-storage-race.txt", "TestAutomaticPurchaseStorageErrors", storage_cases),
    ("linux-peer-final-race.txt", "TestRestartNodeRehearsal", peer_cases),
]:
    text = (results / filename).read_text(encoding="utf-8")
    assert "--- FAIL:" not in text and "WARNING: DATA RACE" not in text, filename
    actual = sorted(re.findall(r"--- PASS: " + test + r"/([^\s]+) \(", text))
    assert actual == sorted(cases), (filename, actual)
    durations[filename] = float(re.findall(r"^--- PASS: " + test + r" \(([\d.]+)s\)", text, re.MULTILINE)[-1])

changed = git("diff", "--name-only", "c62d8cd").splitlines()
assert not [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")]
storage_sources = [
    "tests/restart/purchase_storage_test.go",
    "tests/restart/purchase_recovery_test.go",
    "tests/restart/purchase_crash_recovery_test.go",
]
peer_sources = [
    "tests/restart/purchase_peer_linux_test.go",
    "tests/restart/node_rehearsal_linux_test.go",
]
binaries = [
    "tmp/purchase-storage-windows-tests.exe",
    "tmp/purchase-storage-linux-tests",
    "tmp/purchase-peer-linux-tests",
]
identity = {
    "baseline_commit": git("rev-parse", "c62d8cd"),
    "production_source_changes": False,
    "toolchain": "Go 1.21.3; offline modules; GOMAXPROCS=2; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection and private network namespaces",
    "storage_source_git_blobs": {name: git("hash-object", name) for name in storage_sources},
    "final_peer_source_git_blobs": {name: git("hash-object", name) for name in peer_sources},
    "source_sha256": {name: digest(workspace / name) for name in storage_sources + peer_sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "binary_scope": "The storage binaries precede the final Linux-only peer log-count and empty-pool assertions. Storage source files are identical between builds. The final peer binary includes all recorded final peer assertions.",
    "final_seconds": durations,
    "storage_cases_per_platform": storage_cases,
    "linux_peer_cases": peer_cases,
}
(results / "identities.json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in results.iterdir() if path.is_file() and path.name != "SHA256SUMS")
manifest = "".join(f"{digest(path)}  {path.name}\n" for path in files)
(results / "SHA256SUMS").write_text(manifest, encoding="utf-8", newline="\n")
print(f"Verified final cases and recorded {len(files)} evidence checksums; production source unchanged.")
