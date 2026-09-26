import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
working = workspace / "tmp/full-state-outage-2026-09-26"


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


baseline = git("rev-parse", "fb4039b")
assert baseline in read("environment.txt") and "go version go1.21.3 linux/amd64" in read("environment.txt")
assert read("build.txt") == "" and int(read("outage-exit.txt")) == 0
assert read("binary.sha256").split()[0] == digest(workspace / "tmp/full-state-outage-tests")
data = read("outage-race.txt")
assert "WARNING: DATA RACE" not in data and "--- SKIP:" not in data and "--- FAIL:" not in data
assert data.endswith("PASS\n")
duration = re.findall(r"^--- PASS: TestFullStateSingleProducerOutage \(([0-9.]+)s\)", data, re.MULTILINE)
assert len(duration) == 1
for name in ["prepare-producer", "prepare-verifier", "cold-producer", "cold-verifier"]:
    assert f"--- PASS: TestFullStateSingleProducerOutage/{name} (" in data
cut = re.search(r"isolated for ([^:]+): producer=(\d+) (0x[0-9a-f]+) verifier=(\d+)", data)
saved = re.search(r"SIGKILL pending nonce=(\d+) hash=(0x[0-9a-f]+) signed-bytes=(\d+)", data)
reopen = re.search(r"cold reopen: same saved bytes, canonical nonce=(\d+), empty pool, automatic buying enabled; down=([^\n]+)", data)
recovery = re.search(r"automatic recovery: saved=(0x[0-9a-f]+) successors=(0x[0-9a-f]+)/(0x[0-9a-f]+) common=(\d+) (0x[0-9a-f]+); no raw resubmission, external funding or forced sync", data)
final = re.search(r"single-producer outage passed: final=(\d+) (0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+)", data)
assert cut and saved and reopen and recovery and final
assert int(cut[2]) >= int(cut[4]) + 3 and saved[1] == reopen[1] and saved[2] == recovery[1]
drops = re.search(r"healed partition; netem dropped=(\d+)", data)
assert drops and int(drops[1]) > 0
count = int(final[1]) - 15130080
assert count > 13 and f"blocks={count} totalRewardWei={count * 312500000000000000}; no database opened" in data
assert len(re.findall(r"full-state outage cold (?:producer|verifier) verified:", data)) == 2
assert f"blocks={count} head={final[2]} root={final[3]}" in data
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
for i in range(1, count + 1):
    ledger = json.loads((artifacts / f"block-{i:02d}.json").read_text(encoding="utf-8"))
    assert int(ledger["Header"]["number"], 16) == 15130080 + i
    assert len(ledger["Receipts"]) == 1 and int(ledger["Receipts"][0]["status"], 16) == 1
    if i > 1:
        assert ledger["Header"]["parentHash"] == previous
    previous = ledger["Header"]["hash"]
assert previous == final[2]

manifest = workspace / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS"
assert digest(manifest) == "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf"
source = workspace / "tmp/preserved-head-state"
entries = [line.split("  ./", 1) for line in manifest.read_text(encoding="utf-8").splitlines()]
assert len(entries) == 230
for expected, relative in entries:
    assert digest(source / relative) == expected, relative
capacity = json.loads(read("copy-capacity.json"))
assert capacity["source_files"] == 230 and capacity["copied_bytes"] == 2 * capacity["source_bytes"]
assert capacity["free_bytes_after_copy"] > 50 * 1024**3
results = {"seconds": float(duration[0]), "isolated": cut.groups(), "saved": saved.groups(), "reopen": reopen.groups(), "recovery": recovery.groups(), "packet_drops": int(drops[1]), "final": final.groups(), "suffix_blocks": count, "source_manifest_verified_after_run": True, "scope": "single producer plus verifier; no reorg or manual nonce repair"}
changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
sources = [
    "tests/restart/full_state_outage_linux_test.go", "tests/restart/recovery_nodes_linux_test.go",
    "tests/restart/node_rehearsal_linux_test.go", "tests/restart/network_partition_linux_test.go",
    "tests/restart/partition_miners_linux_test.go", "tests/restart/competing_miners_linux_test.go",
    "tests/restart/purchase_peer_linux_test.go", "tests/restart/full_state_handover_fixture_test.go",
    "tests/restart/full_state_handover_ledger_test.go", "tests/restart/full_state_handover_test.go",
    "tests/restart/full_state_fixture_test.go", "tests/restart/full_state_rehearsal_test.go",
    "tests/restart/blocks_test.go", "tests/restart/fixture_test.go", "consensus/datong/consensus.go",
    "core/state_transition.go", "internal/ethapi/autobuy.go", "go.mod", "go.sum",
    "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS",
    "docs/evidence/restart-full-state-2026-09-24/context.rlp",
    "docs/evidence/restart-2026-09-23/responses.json",
] + [f"docs/evidence/restart-full-state-handover-2026-09-24/windows-blocks/block-{i:02d}.rlp" for i in range(1, 4)]
identities = {"baseline": baseline, "runtime_changed": False, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256": digest(workspace / name)} for name in sources}}
for name, content in [("results.json", results), ("identities.json", identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.relative_to(evidence).as_posix()}\n" for path in files), encoding="utf-8", newline="\n")
print(f"Verified live recovery, {count} suffix blocks, both cold ledgers, all 230 unchanged source files, {len(sources)} source identities and {len(files)} evidence hashes")
