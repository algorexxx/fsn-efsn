import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = subprocess.check_output(["git", "rev-parse", "8d84a04"], cwd=workspace).decode().strip()


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


assert read("initial-exit.txt").strip() == "1"
assert "bounded partition must produce exactly one block and one purchase per owner" in read("initial-race.txt")
assert "txs=0" in read("initial-race.txt")
assert "Automatic ticket purchase confirmed" in read("initial-race.txt")
assert "WARNING: DATA RACE" not in read("initial-race.txt")
assert read("bounded-exit.txt").strip() == "1"
assert "node commitments differ from expected block 15130098" in read("bounded-race.txt")
assert "Number:15130099" in read("bounded-race.txt")
assert "Mining:false" in read("bounded-race.txt")
assert "normal sync converged" in read("bounded-race.txt")
assert "WARNING: DATA RACE" not in read("bounded-race.txt")
assert read("settled-exit.txt").strip() == "1"
assert "outstanding sealing work exceeded the isolated fixture's bound" in read("settled-race.txt")
assert "WARNING: DATA RACE" not in read("settled-race.txt")
assert read("build.txt") == read("initial-build.txt") == read("bounded-build.txt") == read("settled-build.txt") == ""
runs = {}
for label in ["drained", "repeat"]:
    data = read(label + "-race.txt")
    assert read(label + "-exit.txt").strip() == "0", label
    assert "--- PASS: TestRestartNodeRehearsal/partition_purchase_miners" in data, label
    assert not any(marker in data for marker in ["--- FAIL:", "--- SKIP:", "WARNING: DATA RACE"]), label
    assert "both cold heads and exact saved intents agree" in data, label
    assert "stopped miners reached a common head unchanged for 35s" in data, label
    drops = re.findall(r"healed partition; netem dropped=(\d+)", data)
    assert len(drops) == 1 and int(drops[0]) > 0, label
    outage = re.search(r"connected miners partitioned for ([^;]+);", data).group(1)
    duration = float(re.search(r"--- PASS: TestRestartNodeRehearsal/partition_purchase_miners \(([0-9.]+)s\)", data).group(1))
    changes = int(re.search(r"observed (\d+) head changes after stop", data).group(1))
    convergence = re.search(r"normal sync converged in (\S+) to (\d+) (0x[0-9a-f]+)", data)
    final = re.search(r"packet-loss miner recovery passed: final (\d+) (0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+) purchases key1=(\d+) key2=(\d+)", data)
    assert final and convergence and min(int(final[5]), int(final[6])) >= 2, label
    assert int(final[1]) >= int(convergence[2]) + 3, label
    runs[label] = {
        "test_seconds": duration,
        "outage_duration": outage,
        "dropped_packets": int(drops[0]),
        "heal_to_convergence": convergence[1],
        "joined_height": int(convergence[2]),
        "joined_hash": convergence[3],
        "final_height": int(final[1]),
        "final_hash": final[2],
        "state_root": final[3],
        "ticket_root": final[4],
        "native_purchases": [int(final[5]), int(final[6])],
        "head_changes_observed_after_stop": changes,
    }
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", baseline], cwd=workspace).decode().splitlines()
assert not [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")]
source = (workspace / "tests/restart/partition_miners_linux_test.go").read_text(encoding="utf-8")
assert source.count("connectRehearsalPeer(") == 1
assert "lab_sync" not in source and "syncRecoveryNode(" not in source
assert source.index("connectRehearsalPeer(") < source.index("dropRehearsalPackets(")
names = [
    "tests/restart/partition_miners_linux_test.go", "tests/restart/node_rehearsal_linux_test.go",
    "tests/restart/network_partition_linux_test.go", "tests/restart/two_miner_fixture_linux_test.go",
    "tests/restart/purchase_peer_linux_test.go", "tests/restart/competing_miners_linux_test.go",
    "consensus/datong/consensus.go", "core/blockchain.go", "core/tx_pool.go",
    "miner/worker.go", "eth/sync.go", "eth/downloader/downloader.go", "p2p/server.go", "p2p/dial.go",
    "internal/ethapi/autobuy.go",
    "go.mod", "go.sum",
]
binary = workspace / "tmp/miner-partition-linux-tests"
assert digest(binary) == read("binary.sha256").split()[0]
identities = {
    "baseline": baseline,
    "runtime_change": "none; test harness, documentation and evidence only",
    "sources": {name: {
        "git_blob": subprocess.check_output(["git", "-c", "core.safecrlf=false", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(),
        "sha256_raw": digest(workspace / name),
    } for name in names},
    "final_binary_sha256": digest(binary),
    "initial_binary_sha256": read("initial-binary.sha256").split()[0],
    "initial_test_sha256": digest(evidence / "initial-miner-test.go.txt"),
    "bounded_binary_sha256": read("bounded-binary.sha256").split()[0],
    "bounded_test_sha256": digest(evidence / "bounded-miner-test.go.txt"),
    "settled_binary_sha256": read("settled-binary.sha256").split()[0],
    "settled_test_sha256": digest(evidence / "settled-miner-test.go.txt"),
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
result = {
    "result": "Two bounded kernel-loss miner rehearsals pass with Linux race detection",
    "runs": runs,
    "initial_failure": "Fixture assumed the first block contained the purchase; ordinary worker mined an empty block first.",
    "second_failure": "miner_stop reported false before an already-signed block published, invalidating the final snapshot. Observe both stopped heads agreeing without change for 35 seconds before inspecting this two-owner fixture; this is not a universal production drain timeout.",
    "third_failure": "A delayed empty third isolated block exceeded the two-block bound. Inspect after the fault interval and allow one to three blocks while retaining exactly one purchase per isolated owner.",
    "runtime_changes": 0,
    "permanent_patch_inventory": "P1-P15",
    "limits": "Static IPv4 peers in loopback-only namespaces; stop miners after one isolated purchase before healing, then resume. No uninterrupted mining through reorg, deep fork or multi-purchase nonce-gap proof, public networking, real keys, large backup, Windows packet-loss run or full candidate historical replay.",
}
(evidence / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(p) + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified two live miner runs, three retained failed attempts, unchanged runtime and {len(files)} evidence files")
