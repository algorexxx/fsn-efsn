import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", "-c", "core.safecrlf=false", *args], cwd=workspace).decode().strip()


def read(name):
    return (evidence / name).read_text(encoding="utf-8")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


baseline = git("rev-parse", "950f682")
assert all(baseline in read(prefix + "environment.txt") for prefix in ["", "final-", "diagnostic-"])
assert all(read(prefix + "build.txt") == "" for prefix in ["", "final-", "diagnostic-"])
for label, binary in [("binary.sha256", "funded-repair-tests"), ("final-binary.sha256", "funded-repair-final-tests"), ("diagnostic-binary.sha256", "funded-repair-diagnostic-tests")]:
    assert read(label).split()[0] == digest(workspace / "tmp" / binary)
results = {}
for label in ["funded-initial", "funded-wait", "funded-diagnostic", "fixture"]:
    data = read(label + "-race.txt")
    code = int(read(label + "-exit.txt"))
    verdict = re.findall(r"^--- (PASS|FAIL): TestRestartNodeRehearsal \(([0-9.]+)s\)", data, re.MULTILINE)
    assert len(verdict) == 1 and (verdict[0][0] == "PASS") == (code == 0), label
    assert "WARNING: DATA RACE" not in data and "--- SKIP:" not in data, label
    results[label] = {"exit": code, "seconds": float(verdict[0][1]), "data_race_reported": False}
    if label == "fixture":
        assert code == 0 and "complete synthetic genesis-to-24 ancestry independently executed" in data
        continue
    audits = re.findall(r"ledger verified phase=([a-z-]+) range=(\d+)\.\.(\d+) head=(0x[0-9a-f]+)", data)
    assert len([row for row in audits if row[0] == "isolated"]) == 2
    assert len([row for row in audits if row[0] == "before-funding"]) == 1
    gap = re.search(r"stable gap node=(\d+) canonical=(\d+) saved=(\d+) hash=(0x[0-9a-f]+) common=(\d+)", data)
    assert gap and int(gap[3]) > int(gap[2])
    transfers = re.findall(r"funded repair single transfer sender=(0x[0-9a-fA-F]+) recipient=(0x[0-9a-fA-F]+) value-wei=(\d+) hash=(0x[0-9a-f]+) block=(\d+) (0x[0-9a-f]+) gas=21000", data)
    assert len(transfers) == 1 and transfers[0][2] == "5000000000000000000000"
    assert "funded repair confirmed original purchase rejection: insufficient balance" in data
    originals = re.findall(r"original included node=(\d+) nonce=(\d+) hash=(0x[0-9a-f]+) block=(\d+) (0x[0-9a-f]+)", data)
    assert originals and [int(row[1]) for row in originals] == list(range(int(gap[2]), int(gap[2]) + len(originals)))
    retreats = re.findall(r"retreat phase=before-funding block=(\d+) hash=(0x[0-9a-f]+) index=0 owner=(0x[0-9a-fA-F]+) ticket=(0x[0-9a-f]+) start=(\d+) end=(\d+) value-wei=5000000000000000000000 returned=false", data)
    results[label].update({"gap": {"node": int(gap[1]), "canonical_nonce": int(gap[2]), "saved_nonce": int(gap[3]), "saved_hash": gap[4]}, "ledger_audits": audits, "first_retreats_before_funding": retreats, "transfer": dict(zip(["sender", "recipient", "value_wei", "hash", "height", "block_hash"], transfers[0])), "original_purchases_included": len(originals)})
    if label == "funded-initial":
        assert code == 1 and len(originals) == 1 and len(retreats) == 2 and "live repair funding nonce=20 block=38" in data
        assert "insufficient balance(2067602000128000000000)" in data
        assert "live nonce repair passed" not in data and "live repair cold node=" not in data
        assert 7067602042576000000000 - 5000000000000000000000 - 21224 * 2000000000 == 2067602000128000000000
        results[label]["reason"] = "second purchase attempted before the repaired ticket returned usable stake"
    elif label == "funded-wait":
        assert code == 1 and len(originals) == 2 and len(retreats) == 2
        assert "original purchase still unfunded after bounded 60-second wait" in data
        assert "live repair funding nonce=16 block=46" in data
        assert "live nonce repair passed" not in data and "live repair cold node=" not in data
        results[label]["reason"] = "two purchases included; third remained unfunded at the 60-second wait limit"
    elif code == 0:
        assert len(retreats) == 1 and retreats[0][0] == "34"
        assert "funded repair waiting for ordinary ticket return" in data
        assert len(originals) == int(gap[3]) - int(gap[2])
        assert len([row for row in audits if row[0] == "after-repair"]) == 1
        cold = re.findall(r"funded repair cold transfer=(0x[0-9a-f]+) sponsor-nonce=1 sponsor-liquid-wei=999999979000000000000", data)
        assert cold == [transfers[0][3]] * 2
        final = re.search(r"live nonce repair passed: final=(\d+) (0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+) originals=(\d+) automatic-successors=(\d+)", data)
        assert final and int(final[6]) >= 2
        assert len(re.findall(r"live repair cold node=", data)) == 2
        results[label]["final"] = dict(zip(["height", "hash", "state_root", "ticket_root", "originals", "automatic_successors"], final.groups()))
        waits = [float(value) for value in re.findall(r"admitted original nonce=\d+ hash=0x[0-9a-f]+ after-wait=([0-9.]+)s", data)]
        assert len(waits) == 3 and max(waits) < 60
        results[label]["funding_waits_seconds"] = waits
    else:
        raise AssertionError("unexpected diagnostic failure requires explicit classification")

changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
names = [
    "tests/restart/continuous_repair_linux_test.go", "tests/restart/dense_miner_fixture_linux_test.go",
    "tests/restart/node_rehearsal_linux_test.go", "tests/restart/funded_repair_linux_test.go",
    "tests/restart/partition_funds_ledger_linux_test.go", "tests/restart/full_state_handover_ledger_test.go",
    "tests/restart/continuous_partition_linux_test.go", "tests/restart/competing_miners_linux_test.go",
    "tests/restart/network_partition_linux_test.go", "tests/restart/blocks_test.go",
    "tests/restart/fixture_test.go", "consensus/datong/consensus.go", "core/state_transition.go",
    "core/state/statedb.go", "common/fsnargs.go", "common/timelock.go", "common/ticket.go",
    "internal/ethapi/autobuy.go", "internal/ethapi/api_fsn.go", "go.mod", "go.sum",
]
identities = {"baseline": baseline, "runtime_changed": False, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256": digest(workspace / name)} for name in names}}
for name, content in [("results.json", results), ("identities.json", identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.name}\n" for path in files), encoding="utf-8", newline="\n")
print(f"Verified {len(results)} completed runs, {len(names)} source identities, {len(files)} evidence hashes and unchanged production source/dependencies")
