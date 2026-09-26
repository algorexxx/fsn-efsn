import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
working = workspace / "tmp/full-state-participant-2026-09-26-attempt-03"


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


baseline = git("rev-parse", "4afa625")
assert baseline in read("environment.txt") and "go version go1.21.3 linux/amd64" in read("environment.txt")
assert read("build.txt") == "" and int(read("participant-attempt-03-exit.txt")) == 0
assert read("binary.sha256").split()[0] == digest(workspace / "tmp/full-state-participant-tests")
assert read("attempt-01/binary.sha256").split()[0] == digest(workspace / "tmp/full-state-participant-attempt-01-tests")
failed = read("participant-race.txt")
assert int(read("participant-exit.txt")) == 1 and "BuyTicket start must be lower than latest block time + 3 hour" in failed
assert "--- FAIL: TestFullStateParticipantEntry (26.17s)" in failed
assert read("attempt-02/binary.sha256").split()[0] == digest(workspace / "tmp/full-state-participant-attempt-02-tests")
assert int(read("participant-attempt-02-exit.txt")) == 1
assert "only public rehearsal keys 1 and 2 are permitted" in read("participant-attempt-02-race.txt")
data = read("participant-attempt-03-race.txt")
assert "WARNING: DATA RACE" not in data and "--- SKIP:" not in data and "--- FAIL:" not in data and data.endswith("PASS\n")
duration = re.findall(r"^--- PASS: TestFullStateParticipantEntry \(([0-9.]+)s\)", data, re.MULTILINE)
assert len(duration) == 1
for name in ["prepare-producer", "prepare-verifier", "fund-producer", "fund-verifier", "cold-producer", "cold-verifier"]:
    assert f"--- PASS: TestFullStateParticipantEntry/{name} (" in data
assert "both owners bought and signed canonical blocks" in data
final = re.search(r"participant entry passed: final=(\d+) (0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+) blocks=(\d+)", data)
assert final
count = int(final[5])
assert count == int(final[1]) - 15130080 and count >= 9
assert len(re.findall(r"full-state outage cold (?:producer|verifier) verified:", data)) == 2
assert f"blocks={count} head={final[2]} root={final[3]}" in data
assert f"participant ledger passed: blocks={count-3} ordinary-conversions=1 ordinary-transfers=1" in data
assert "blocks=3 totalRewardWei=937500000000000000; no database opened" in data
artifacts = evidence / "artifacts"
artifacts.mkdir(exist_ok=True)
paths = sorted((working / "blocks").glob("block-*.*"))
assert len(paths) == count * 2
paths += [working / "producer/fixture.json", working / "producer/handover.json"]
for path in paths:
    target = artifacts / path.name
    if target.exists():
        assert digest(target) == digest(path), target
    else:
        shutil.copyfile(path, target)
signers = {}
transactions = 0
for i in range(1, count + 1):
    ledger = json.loads((artifacts / f"block-{i:02d}.json").read_text(encoding="utf-8"))
    assert int(ledger["Header"]["number"], 16) == 15130080 + i
    for receipt in ledger["Receipts"]:
        assert int(receipt["status"], 16) == 1
    transactions += len(ledger["Receipts"])
    if i > 1:
        assert ledger["Header"]["parentHash"] == previous
    if i > 6:
        signer = ledger["Header"]["miner"]
        signers[signer] = signers.get(signer, 0) + 1
    previous = ledger["Header"]["hash"]
assert previous == final[2]
assert set(signers) == {"0x2b5ad5c4795c026514f8317c7a215e218dccd6cf", "0x6813eb9362372eef6200f3b1dbc3f819671cba69"}
manifest = workspace / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS"
assert digest(manifest) == "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf"
entries = [line.split("  ./", 1) for line in manifest.read_text(encoding="utf-8").splitlines()]
assert len(entries) == 230
for expected, relative in entries:
    assert digest(workspace / "tmp/preserved-head-state" / relative) == expected, relative
for name in ["copy-capacity.json", "attempt-01/copy-capacity.json", "attempt-02/copy-capacity.json"]:
    capacity = json.loads(read(name))
    assert capacity["source_files"] == 230 and capacity["copied_bytes"] == 1057634160
    assert capacity["free_bytes_after_copy"] > 50 * 1024**3
changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
sources = list(json.loads((workspace / "docs/evidence/restart-full-state-outage-2026-09-26/identities.json").read_text(encoding="utf-8"))["sources"])
sources += ["tests/restart/full_state_participant_linux_test.go", "tests/restart/full_state_participant_ledger_test.go", "tests/restart/continuous_partition_linux_test.go", "common/fsnparams.go", "common/fsntypes.go"]
identities = {"baseline": baseline, "runtime_changed": False, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256": digest(workspace / name)} for name in sources}}
results = {"seconds": float(duration[0]), "final": final.groups(), "live_canonical_signers": signers, "transactions": transactions, "source_files_unchanged": 230, "copied_bytes_all_attempts": 3172902480, "failed_attempt_seconds": [26.17, 29.61], "scope": "funded participant entry and shared production, no deliberate partition or nonce repair"}
for name, content in [("results.json", results), ("identities.json", identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.relative_to(evidence).as_posix()}\n" for path in files), encoding="utf-8", newline="\n")
print(f"Verified both cold ledgers, {count} suffix blocks, {transactions} transactions, all 230 unchanged source files, {len(sources)} source identities and {len(files)} evidence hashes; retained both failed attempts")
