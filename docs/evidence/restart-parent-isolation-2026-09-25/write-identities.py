import hashlib
import json
import re
import subprocess
from pathlib import Path


evidence = Path(__file__).resolve().parent
root = evidence.parents[2]
rollback = evidence.parent / "restart-purchase-rollback-2026-09-25"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=root).decode("utf-8").strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_log(folder, name):
    return (folder / name).read_text(encoding="utf-8-sig")


def passed(text, test, count=1, indent=""):
    pattern = rf"^{indent}--- PASS: {re.escape(test)} \("
    actual = len(re.findall(pattern, text, re.MULTILINE))
    assert actual == count, (test, actual, count)


def clean_pass(text):
    assert text.rstrip().endswith("\nPASS"), "missing final PASS"
    assert "WARNING: DATA RACE" not in text
    assert "--- FAIL:" not in text


production = [
    "consensus/datong/consensus.go",
    "core/blockchain.go",
    "core/headerchain.go",
]
tests = [
    "tests/restart/finalize_parent_test.go",
    "tests/restart/two_miner_fixture_linux_test.go",
    "tests/restart/purchase_nonce_rollback_linux_test.go",
    "tests/restart/competing_miners_linux_test.go",
    "tests/restart/node_rehearsal_linux_test.go",
    "tests/restart/preserved_reconstruction_test.go",
]
baseline = git("rev-parse", "bcbd1ce")
changed = git("diff", "--name-only", baseline, "--", "*.go").splitlines()
assert sorted(p for p in changed if not p.endswith("_test.go")) == sorted(production)
counts = git("diff", "--numstat", baseline, "--", *production).splitlines()
assert sum(int(line.split()[0]) for line in counts) == 5
assert sum(int(line.split()[1]) for line in counts) == 22
assert not git("diff", baseline, "--", "core/bench_test.go", "core/gaspool.go", "core/gas.go", "core/state_transition.go")

before = read_log(evidence, "windows-before.txt")
assert before.count("importing chain's parent: unknown ancestor") == 2
assert "--- FAIL: TestFinalizeParentIsolatedFromConcurrentImport" in before
race = read_log(rollback, "pre-fix-competing-race.txt")
assert race.count("WARNING: DATA RACE") == 2
assert "SetHeaders" in race and "Finalize" in race
assert "--- FAIL: TestRestartNodeRehearsal (84.37s)" in race

for name in ["windows-after.txt", "linux-parent-race.txt"]:
    text = read_log(evidence, name)
    clean_pass(text)
    passed(text, "TestFinalizeParentIsolatedFromConcurrentImport", 5)
    passed(text, "TestHeaderBatchUsesUnstoredParents", 5)

anchors = [
    "heavier_fork", "checkpoint_direct", "checkpoint_stored_fork",
    "checkpoint_headers", "checkpoint_receipts", "checkpoint_commit_head",
    "checkpoint_startup", "checkpoint_late_init", "checkpoint_body_shortcut",
]
text = read_log(evidence, "linux-anchor-race.txt")
clean_pass(text)
passed(text, "TestRestartAnchorEntryPointsCharacterization")
for case in anchors:
    passed(text, "TestRestartAnchorEntryPointsCharacterization/" + case, indent="    ")

nodes = [
    "readiness_mining_crash", "compatible_peer", "purchase_peer_nonce_rollback",
    "heavier_stored_fork_peer", "incompatible_database_startup",
]
text = read_log(evidence, "linux-node-regressions-race.txt")
assert text.rstrip().endswith("\nPASS") and "WARNING: DATA RACE" not in text
passed(text, "TestRestartNodeRehearsal")
for case in nodes:
    passed(text, "TestRestartNodeRehearsal/" + case, indent="    ")
assert "purchase_peer_nonce_rollback (49.95s)" in text

text = read_log(rollback, "linux-competing-race.txt")
clean_pass(text)
passed(text, "TestRestartNodeRehearsal")
passed(text, "TestRestartNodeRehearsal/competing_purchase_miners", indent="    ")
assert "TestRestartNodeRehearsal (98.37s)" in text
core = read_log(evidence, "linux-core-race.txt")
assert "core/bench_test.go" in core and "[build failed]" in core
assert "IntrinsicGas" in core and "CalcGasLimit" in core

binaries = {
    "tmp/parent-isolation-before-windows-tests.exe": "Pre-P9 production and baseline-test.go.txt; expected functional failure.",
    "tmp/parent-isolation-windows-tests.exe": "Final P9 production and both final deterministic regressions; Windows five repeats each.",
    "tmp/parent-isolation-linux-tests": "Final P9 production and listed tests; Linux race checks, anchor cases and five-node group.",
    "tmp/purchase-competing-linux-tests": "Final P9 production and final miner/rollback sources; predates added header-batch regression in finalize_parent_test.go; Linux competing-miner pass.",
}
identities = {
    "date": "2026-09-25",
    "baseline_commit": baseline,
    "source_identity_scope": "Final working sources below. Earlier failed/preparation runs are historical evidence, not asserted to use these final test blobs.",
    "production_diff": {"added_lines": 5, "removed_lines": 22, "paths": production},
    "sources": {
        name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": sha256(root / name)}
        for name in production + tests
    },
    "binaries": {
        name: {"sha256": sha256(root / name), "scope": scope}
        for name, scope in binaries.items()
    },
    "before_race_binary": json.loads(read_log(evidence, "race-binary-before.json")),
    "verified_results": {
        "baseline_independent_unknown_ancestor_errors": 2,
        "pre_fix_real_miner_race_reports": 2,
        "deterministic_cases_per_platform": 2,
        "repeats_per_deterministic_case_per_platform": 5,
        "anchor_cases": anchors,
        "actual_node_cases": nodes,
        "actual_node_group_seconds": 79.68,
        "final_rollback_seconds": 49.95,
        "final_competing_miners_seconds": 98.37,
        "broader_core_tests": "Not run: package failed to compile due to unchanged legacy test APIs; raw failure retained.",
    },
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
for folder in [evidence, rollback]:
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    lines = [sha256(p) + "  " + p.name for p in files]
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Verified and checksummed {len(files)} files in {folder.name}")
print("Recorded expected baseline failures, final passing regressions, and legacy core build limitation.")
