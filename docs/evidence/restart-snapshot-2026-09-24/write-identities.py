from pathlib import Path
import json
import subprocess
import sys

workspace = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(workspace / "tests/restart"))
import snapshot_package

evidence = Path(__file__).parent
assert json.loads((evidence / "pipeline-status.json").read_text(encoding="utf-8"))["status"] == "passed"
sources = ["tests/restart/" + name for name in ["snapshot_package.py", "snapshot_package_test.py",
           "snapshot_package_test.go", "snapshot_indexes_test.go", "snapshot_service_test.go"]]
binaries = ["tmp/" + name for name in ["snapshot-package-windows-tests.exe",
            "snapshot-indexes-windows-tests.exe", "snapshot-restore-windows-tests.exe"]]
packer = "tests/restart/snapshot_package.py"
raw_blob = subprocess.check_output(["git", "hash-object", "--no-filters", packer], cwd=workspace, text=True).strip()
git_blob = subprocess.check_output(["git", "hash-object", "--path=" + packer, packer], cwd=workspace, text=True).strip()
assert raw_blob == git_blob, "Git normalization changes the exact packer bytes pinned by the source plan"
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "0ad0136"], cwd=workspace, text=True).strip(),
    "python": sys.version,
    "go": subprocess.check_output([str(workspace / "tmp/restart-runtime/go/bin/go.exe"), "version"], cwd=workspace, text=True).strip(),
    "windows_build": {"CGO_ENABLED": "0", "GOMAXPROCS": "2", "GOTOOLCHAIN": "local", "GOPROXY": "off", "flags": "-p=2 -mod=readonly"},
    "working_tree_source_sha256": {name: snapshot_package.digest(workspace / name) for name in sources},
    "packer_source_git_blob": git_blob,
    "packer_source_matches_git_filter": True,
    "binary_sha256": {name: snapshot_package.digest(workspace / name) for name in binaries},
    "note": "Source hashes describe the final working-tree bytes. Packaging and source-index binaries were built earlier in the same investigation; later additions affect other tests. This is not a reproducible release-build attestation. No production Go source changed in this follow-up."
}
snapshot_package.write_json(evidence / "identities.json", report)
print(json.dumps(report, indent=2))
