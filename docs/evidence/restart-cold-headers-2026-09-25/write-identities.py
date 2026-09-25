import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=workspace).decode("utf-8").strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


baseline = git("rev-parse", "04ad861")
changed_go = git("diff", "--name-only", baseline, "--", "*.go").splitlines()
assert all(path.endswith("_test.go") for path in changed_go), changed_go
previous = git("diff", "--name-only", "bcbd1ce", baseline, "--", "*.go").splitlines()
assert sorted(path for path in previous if not path.endswith("_test.go")) == [
    "consensus/datong/consensus.go", "core/blockchain.go", "core/headerchain.go"
]
cases = [
    "headers_only", "headers_receipts", "headers_bodies", "headers_complete",
    "headers_missing_receipt", "headers_incremental", "invalid_header", "full_import",
]
logs = ["windows-current.txt", "windows-pre-p9.txt", "linux-race.txt"]
results = {}
for name in logs:
    text = (evidence / name).read_text(encoding="utf-8-sig")
    assert text.rstrip().endswith("\nPASS"), name
    assert "WARNING: DATA RACE" not in text and "--- FAIL:" not in text, name
    for case in cases:
        pattern = rf"^    --- PASS: TestColdHeaderValidationBoundaries/{case} \("
        assert len(re.findall(pattern, text, re.MULTILINE)) == 1, (name, case)
    for case in ["headers_only", "headers_receipts", "headers_bodies", "headers_missing_receipt", "headers_incremental"]:
        index = 0 if case == "headers_incremental" else 1
        assert f'cold {case}: index={index} err="AddCachedTickets: hash mismatch"' in text, (name, case)
    assert 'cold headers_complete: index=0 err=""' in text, name
    assert 'cold invalid_header: index=1 err="invalid gasUsed:' in text, name
    assert text.count("cold full import/reopen agrees on three canonical blocks") == 2, name
    duration = re.findall(r"^--- PASS: TestColdHeaderValidationBoundaries \(([^)]+)\)", text, re.MULTILINE)
    assert len(duration) == 1, name
    results[name] = {"cases": 8, "duration": duration[0], "expected_incomplete_reconstruction_rejections": 5, "expected_invalid_header_rejections": 1, "cold_full_import_and_reopen": True}

sources = [
    "tests/restart/header_sync_cold_test.go", "tests/restart/fixture_test.go",
    "tests/restart/autobuy_test.go", "tests/restart/anchor_paths_test.go",
    "consensus/datong/consensus.go", "core/blockchain.go", "core/headerchain.go",
    "core/state/statedb.go", "core/rawdb/accessors_chain.go", "eth/downloader/modes.go",
    "eth/downloader/downloader.go", "eth/sync.go", "eth/ethconfig/config.go", "light/lightchain.go",
]
binaries = {
    "tmp/cold-headers-current-windows-tests.exe": "Current candidate production; new eight-case test, Windows without race detection.",
    "tmp/cold-headers-pre-p9-windows-tests.exe": "Same new test; three P9 runtime files overlaid with pre-P9 bytes, Windows without race detection.",
    "tmp/cold-headers-linux-tests": "Current candidate production; new eight-case test, Linux with race detection.",
}
identities = {
    "date": "2026-09-25",
    "candidate_baseline": baseline,
    "production_changes_this_investigation": [],
    "comparison": json.loads((evidence / "baseline-sources.json").read_text(encoding="utf-8")),
    "current_sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": sha256(workspace / name)} for name in sources},
    "binaries": {name: {"sha256": sha256(workspace / name), "scope": scope} for name, scope in binaries.items()},
    "results": results,
    "limits": "Characterizes expected refusals; no network fast sync, genesis resync, full-history replay or real-key/backup use. Stored receipt/body preparation is synthetic.",
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(sha256(path) + "  " + path.name for path in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified 8 cases in each of 3 runs; checksummed {len(files)} evidence files. No production changes.")
