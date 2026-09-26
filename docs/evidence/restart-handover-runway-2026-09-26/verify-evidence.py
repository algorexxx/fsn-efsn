import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
original = workspace / "docs/evidence/restart-full-state-handover-2026-09-24"


def git(*args):
    return subprocess.check_output(["git", "-c", "core.safecrlf=false", *args], cwd=workspace).decode().strip()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def read(name):
    return (evidence / name).read_text(encoding="utf-8")


baseline = git("rev-parse", "ed72295")
for prefix, binary in [("", "handover-runway-tests"), ("final-", "handover-runway-final-tests")]:
    assert baseline in read(prefix + "environment.txt")
    assert read(prefix + "build.txt") == ""
    assert read(prefix + "binary.sha256").split()[0] == digest(workspace / "tmp" / binary)
initial = read("runway-race.txt")
final = read("final-race.txt")
assert int(read("runway-exit.txt")) == 1 and int(read("final-exit.txt")) == 0
assert "--- FAIL: TestPreservedHandoverFundingCoverage (" in initial
assert initial.count("handover coverage assumes the recorded no-retreat sequence") == 2
assert "--- FAIL:" not in final and final.endswith("PASS\n")
for data in [initial, final]:
    assert "WARNING: DATA RACE" not in data and "--- SKIP:" not in data
assert len(re.findall(r"^--- PASS: TestPreservedHandoverFundingCoverage \(", final, re.MULTILINE)) == 1

input_manifest = dict(line.split("  ", 1)[::-1] for line in (original / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
inputs = []
results = {}
for platform in ["windows", "linux"]:
    paths = [original / (platform + "-fixture.json"), original / (platform + "-handover.json")]
    paths += sorted((original / (platform + "-blocks")).glob("block-*.*"))
    assert len(paths) == 22
    for path in paths:
        assert digest(path) == input_manifest[path.relative_to(original).as_posix()], path
        inputs.append(path.relative_to(workspace).as_posix())
    section = final.split("=== RUN   TestPreservedHandoverFundingCoverage/" + platform + "\n", 1)[1].split("=== RUN   TestPreservedHandoverFundingCoverage/", 1)[0]
    assert f"--- PASS: TestPreservedHandoverFundingCoverage/{platform} (" in final
    rows = re.findall(r"handover coverage block=(\d+) hash=(0x[0-9a-f]+) nonce=(\d+) purchase-start=(\d+) purchase-end=(\d+) before-lock-min-wei=(\d+) gas-budget-wei=(\d+) after-liquid-wei=(\d+) next-30-day-lock-min-wei=(\d+) selected=(0x[0-9a-f]+) retreats=(\d+) successor-retreats=0", section)
    assert len(rows) == 10 and [int(row[0]) for row in rows] == list(range(1, 11))
    assert [int(row[2]) for row in rows] == list(range(1, 11))
    assert [row[5] for row in rows] == ["0"] * 2 + ["5000000000000000000000"] * 8
    assert [int(row[10]) for row in rows] == [6, 5, 4] + [0] * 7
    assert rows[-1][7] == str(12020102000000000000000 - 10000000000000000000000 - 42448000000000 + 9 * 312500000000000000)
    assert all(int(row[4]) - int(row[3]) == 30*24*3600 for row in rows[2:])
    projections = re.findall(r"handover frozen-state projection days=(\d+) start=(\d+) end=(\d+) liquid-wei=(\d+) lock-min-wei=(\d+) interval-live-tickets=(\d+)", section)
    assert len(projections) == 6 and [int(row[0]) for row in projections] == [0, 1, 7, 29, 30, 31]
    assert [row[4] for row in projections] == ["5000000000000000000000"] * 4 + ["10000000000000000000000"] * 2
    assert [int(row[5]) for row in projections] == [1, 1, 1, 1, 0, 0]
    assert "blocks=10 totalRewardWei=3125000000000000000; no database opened" in section
    results[platform] = {"blocks": rows, "frozen_state_samples": projections, "new_database_execution": False}

changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
sources = [
    "tests/restart/handover_runway_test.go", "tests/restart/full_state_handover_ledger_test.go",
    "tests/restart/full_state_handover_fixture_test.go", "tests/restart/full_state_fixture_test.go",
    "tests/restart/fixture_test.go", "common/timelock.go", "common/fsntypes.go", "common/fsnargs.go",
    "core/tx_pool.go", "core/state_transition.go", "consensus/datong/consensus.go",
    "internal/ethapi/api_fsn.go", "internal/ethapi/autobuy.go", "go.mod", "go.sum",
    "docs/evidence/restart-2026-09-23/responses.json",
    "docs/evidence/restart-full-state-handover-2026-09-24/SHA256SUMS",
] + inputs
identities = {"baseline": baseline, "runtime_changed": False, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256": digest(workspace / name)} for name in sources}}
for name, content in [("results.json", results), ("identities.json", identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.name}\n" for path in files), encoding="utf-8", newline="\n")
print(f"Verified 44 original input hashes, 20 block ledgers, 12 frozen-state samples, retained failed assertion, {len(sources)} source/input identities and {len(files)} evidence hashes")
