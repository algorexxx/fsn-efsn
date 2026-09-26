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


for name in ["build.txt", "final-build.txt", "record-build.txt"]:
    assert read(name) == "", name
assert "module lookup disabled" in read("record-initial-build.txt")
assert read("record-package-build.txt").count("undefined: tmpdir") == 3
results = {}
for label, code in {"rpc-initial": 0, "small-initial": 1, "rich-initial": 1, "small-final": 1, "rich-final": 0, "record": 0}.items():
    data = read(label + "-race.txt")
    assert read(label + "-exit.txt").strip() == str(code), label
    assert "--- SKIP:" not in data and "WARNING: DATA RACE" not in data, label
    assert ("--- FAIL:" in data) == (code != 0), label
    durations = re.findall(r"--- (?:PASS|FAIL): Test(?:RestartNodeRehearsal|RestartPurchaseRecordCommand) \(([0-9.]+)s\)", data)
    assert durations, label
    results[label] = {"exit": code, "test_seconds": float(durations[-1])}
rpc = read("rpc-initial-race.txt")
locations = re.findall(r"displaced purchase RPC recovered nonce=(\d+) hash=(0x[0-9a-f]+) bytes=(\d+) old-block=(\d+) (0x[0-9a-f]+) index=(\d+) replacement=(0x[0-9a-f]+)", rpc)
assert len(locations) == 2 and locations[0] == locations[1]
assert rpc.count("transaction-hash lookup and receipt absent; invalid locations return null") == 2
assert "restored nonce 16 and exact saved successor" in rpc
assert "--- PASS: TestRestartNodeRehearsal/dense_miner_fixture" in rpc
results["rpc-initial"]["retrieval"] = dict(zip(["nonce", "hash", "bytes", "old_height", "old_hash", "index", "canonical_hash"], locations[0]))
for label in ["small-initial", "small-final"]:
    data = read(label + "-race.txt")
    assert "healed partition; netem dropped=44" in data
    assert "phase=paused-before-repair" in data
    assert re.search(r"phase=paused-before-repair block=\d+ owner=1 stored=0 valid-next-period=0", data)
    assert re.search(r"phase=paused-before-repair block=\d+ owner=2 stored=1 valid-next-period=1", data)
    assert "live repair original included" not in data and "live nonce repair passed" not in data
    gap = re.search(r"stable gap node=(\d+) canonical=(\d+) saved=(\d+) hash=(0x[0-9a-f]+) common=(\d+)", data)
    assert gap and int(gap[3]) > int(gap[2])
    balance = re.search(r"insufficient balance\((\d+)\), need (\d+)", data)
    assert balance and int(balance[1]) < int(balance[2])
    states = re.findall(r"continuous node=(\d+) height=(\d+) hash=(0x[0-9a-f]+) nonce=(\d+) saved=(0x[0-9a-f]+) nonce=(\d+) pending=(\d+) queued=(\d+) mining=(true|false) autobuy=(true|false)", data)
    assert len(states) == 2 and states[0][1:3] == states[1][1:3]
    assert all(item[8:] == ("true", "true") for item in states)
    results[label].update({"reason": "insufficient funding for first missing purchase", "gap": {"node": int(gap[1]), "canonical_nonce": int(gap[2]), "saved_nonce": int(gap[3]), "saved_hash": gap[4], "common_block": int(gap[5])}, "head": {"height": int(states[0][1]), "hash": states[0][2]}, "liquid_wei": balance[1], "required_wei": balance[2], "manual_repair_admitted": False, "cold_acceptance_reached": False})
small = read("small-final-race.txt")
funding = re.search(r"live repair funding nonce=(\d+) block=(\d+) owner=(0x[0-9a-fA-F]+) liquid-wei=(\d+) covers-current-interval=(true|false) timelocks=(\[.*\])", small)
assert funding and funding[5] == "false"
assert "miner resumed automatically node=1" in small
results["small-final"]["time_locks"] = json.loads(funding[6])
assert "ordinary miner and automatic buyer must remain enabled" in read("rich-initial-race.txt")
assert "Mining aborted due to sync" in read("rich-initial-race.txt")
results["rich-initial"]["reason"] = "harness rejected the ordinary downloader-induced worker pause"
rich = read("rich-final-race.txt")
assert "live nonce repair passed" in rich
assert len(re.findall(r"live repair cold node=", rich)) == 2
originals = re.findall(r"original included node=(\d+) nonce=(\d+) hash=(0x[0-9a-f]+) block=(\d+) (0x[0-9a-f]+)", rich)
assert len(originals) >= 1
assert [int(item[1]) for item in originals] == list(range(int(originals[0][1]), int(originals[-1][1]) + 1))
successors = int(re.search(r"resumed with (\d+) new automatic successors", rich)[1])
assert successors >= 2
results["rich-final"].update({"originals": len(originals), "automatic_successors": successors, "cold_nodes": 2})
record = read("record-race.txt")
assert "preserved exact signed purchase nonce=17" in record and "all database file hashes" in record
assert "missing record and locked database rejected" in record
assert record.count("db get result=exit status 1") == 2 and "db get result=<nil>" in record
baseline = git("rev-parse", "c79b227")
assert baseline in read("environment.txt") and baseline in read("final-environment.txt")
changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
names = ["tests/restart/continuous_repair_linux_test.go", "tests/restart/dense_miner_fixture_linux_test.go", "tests/restart/displaced_purchase_rpc_linux_test.go", "tests/restart/purchase_record_command_linux_test.go", "tests/restart/node_rehearsal_linux_test.go", "tests/restart/purchase_nonce_rollback_linux_test.go", "tests/restart/continuous_partition_linux_test.go", "common/ticket.go", "common/fsnparams.go", "consensus/datong/consensus.go", "core/blockchain.go", "core/tx_pool.go", "core/state_transition.go", "miner/miner.go", "internal/ethapi/api.go", "internal/ethapi/api_fsn.go", "internal/ethapi/autobuy.go", "eth/api_backend.go", "cmd/efsn/dbcmd.go", "cmd/utils/flags.go", "go.mod", "go.sum"]
binaries = {"initial": ("tmp/small-reserve-repair-tests", "initial-binary.sha256"), "final": ("tmp/small-reserve-final-tests", "final-binary.sha256"), "command": ("tmp/purchase-record-efsn", "record-binary.sha256")}
for path, checksum in binaries.values():
    assert digest(workspace / path) == read(checksum).split()[0]
identities = {"baseline": baseline, "runtime_changes": 0, "dependency_changes": 0, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": digest(workspace / name)} for name in names}, "binaries": {label: digest(workspace / item[0]) for label, item in binaries.items()}, "initial_source_override": {"tests/restart/continuous_repair_linux_test.go": "initial-continuous-repair.go.txt"}, "initial_excluded_test_file": "tests/restart/purchase_record_command_linux_test.go", "abandoned_command_package_test": "record-initial-command-test.go.txt"}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
summary = {"results": results, "runtime_changes": 0, "patch_inventory": "P1-P15", "scope": "RPC retrieval and existing offline command pass; generous repair passes after harness correction; two small-reserve funding failures retained. Synthetic devnet results are not complete-state donation-wallet reserve accounting. No public peers, original backup or real keys."}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(path) + "  " + path.name for path in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified retrieval/command passes, two small funding failures, corrected rich repair, unchanged runtime/dependencies and {len(files)} evidence checksums")
