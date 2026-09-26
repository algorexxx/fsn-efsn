import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = subprocess.check_output(["git", "rev-parse", "0148d5e"], cwd=workspace).decode().strip()


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


assert read("build.txt") == read("strict-build.txt") == ""
assert baseline in read("environment.txt")
for label in ["fixture-initial", "fixture-final"]:
    data = read(label + "-race.txt")
    assert read(label + "-exit.txt").strip() == "0", label
    assert "complete synthetic genesis-to-24 ancestry independently executed" in data
    assert "--- PASS: TestRestartNodeRehearsal/dense_miner_fixture" in data
    assert not any(x in data for x in ["--- FAIL:", "--- SKIP:", "WARNING: DATA RACE"])
regression = read("regression-race.txt")
assert read("regression-exit.txt").strip() == "0"
for case in ["dense_miner_fixture", "heavier_stored_fork_peer"]:
    assert "--- PASS: TestRestartNodeRehearsal/" + case in regression
assert not any(x in regression for x in ["--- FAIL:", "--- SKIP:", "WARNING: DATA RACE"])
runs = {}
for label in ["live-initial", "live-strict"]:
    data = read(label + "-race.txt")
    assert read(label + "-exit.txt").strip() == "1", label
    assert "--- FAIL: TestRestartNodeRehearsal/continuous_partition_miners" in data
    assert "but both owners did not replenish" in data
    assert "needs nonce" in data
    assert not any(x in data for x in ["--- SKIP:", "WARNING: DATA RACE", "multiple headers (0) for single request"])
    drops = [int(x) for x in re.findall(r"healed partition; netem dropped=(\d+)", data)]
    assert len(drops) == (2 if label == "live-initial" else 1) and min(drops) > 0
    states = re.findall(r"continuous node=(\d+) height=(\d+) hash=(0x[0-9a-f]+) nonce=(\d+) saved=(0x[0-9a-f]+) nonce=(\d+) pending=(\d+) queued=(\d+) mining=(true|false) autobuy=(true|false)", data)
    assert len(states) == (6 if label == "live-initial" else 4), (label, states)
    final = [{"node": int(s[0]), "height": int(s[1]), "hash": s[2], "canonical_nonce": int(s[3]), "saved_hash": s[4], "saved_nonce": int(s[5]), "pending": int(s[6]), "queued": int(s[7]), "mining": s[8] == "true", "autobuy": s[9] == "true"} for s in states[-2:]]
    assert all(s["mining"] and s["autobuy"] for s in final)
    assert any(s["saved_nonce"] > s["canonical_nonce"] and s["pending"] == s["queued"] == 0 for s in final)
    shared = re.search(r"continuous miners share block (\d+) (0x[0-9a-f]+) but both owners did not replenish above (\d+)", data)
    assert shared and int(shared[1]) > int(shared[3])
    duration = float(re.search(r"--- FAIL: TestRestartNodeRehearsal/continuous_partition_miners \(([0-9.]+)s\)", data)[1])
    runs[label] = {"result": "FAIL: unattended replenishment requirement", "test_seconds": duration, "kernel_drops": drops, "shared_advancing_block": {"number": int(shared[1]), "hash": shared[2]}, "purchase_floor": int(shared[3]), "final_observations": final}
probe = runs["live-initial"]["final_observations"]
assert probe[0]["canonical_nonce"] == 28 and probe[0]["saved_nonce"] == 32
assert probe[0]["hash"] == probe[1]["hash"] and probe[0]["height"] == probe[1]["height"] == 53
assert read("live-initial-race.txt").count("nonce=28 saved=" + probe[0]["saved_hash"] + " nonce=32") == 2
strict = runs["live-strict"]["final_observations"]
assert strict[0]["canonical_nonce"] == 28 and strict[0]["saved_nonce"] == 30
assert strict[0]["hash"] == strict[1]["hash"] and strict[0]["height"] == strict[1]["height"] == 47
assert "at nonces >=" in read("live-strict-race.txt")
source = (workspace / "tests/restart/continuous_partition_linux_test.go").read_text(encoding="utf-8")
assert "tx.Nonce() >= requiredNonces[i]" in source
assert source.count("connectRehearsalPeer(") == 1
assert source.index("connectRehearsalPeer(") < source.index("dropRehearsalPackets(")
assert "lab_sync" not in source and "syncRecoveryNode(" not in source
assert source.index("stopPeerAutoMiner(") > source.index("recovered without stopping miners")
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", baseline], cwd=workspace).decode().splitlines()
assert not [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")]
names = ["tests/restart/continuous_partition_linux_test.go", "tests/restart/dense_miner_fixture_linux_test.go", "tests/restart/node_rehearsal_linux_test.go", "tests/restart/partition_miners_linux_test.go", "tests/restart/network_partition_linux_test.go", "tests/restart/blocks_test.go", "tests/restart/purchase_peer_linux_test.go", "tests/restart/competing_miners_linux_test.go", "tests/restart/purchase_nonce_rollback_linux_test.go", "common/fork.go", "core/genesis.go", "params/config.go", "consensus/datong/consensus.go", "core/blockchain.go", "core/tx_pool.go", "internal/ethapi/autobuy.go", "miner/worker.go", "eth/sync.go", "eth/downloader/downloader.go", "go.mod", "go.sum"]
binaries = {"probe": "tmp/continuous-partition-linux-tests", "strict": "tmp/continuous-partition-strict-tests"}
for label, path in binaries.items():
    assert digest(workspace / path) == read(label + "-binary.sha256").split()[0]
identities = {"baseline": baseline, "runtime_changes": 0, "sources": {name: {"git_blob": subprocess.check_output(["git", "-c", "core.safecrlf=false", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(), "sha256_raw": digest(workspace / name)} for name in names}, "binaries": {label: digest(workspace / path) for label, path in binaries.items()}, "initial_fixture_binary_sha256": read("fixture-initial-binary.sha256").split()[0], "probe_source": "probe-live-test.go.txt", "initial_fixture_source": "initial-live-test.go.txt"}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
summary = {"result": "Complete fixture passes; uninterrupted miners reconnect and advance, but unattended automatic replenishment fails with a nonce gap", "runs": runs, "strict_second_outage_reached": False, "live_cold_acceptance_reached": False, "probe_oracle_limit": "Initial first-cycle marker only checked a purchase's inclusion and could count reinclusion of an old transaction. It does not establish restored auto-buy. Final oracle requires a purchase at or beyond each wallet's pre-heal canonical nonce.", "runtime_changes": 0, "patch_inventory": "P1-P15", "limits": "Complete small synthetic devnet with forks active at genesis; real mainnet rewards/funding/history, public networking and live manual repair are separate. No production keys or large backup used. Both live attempts are retained as failures, not passes."}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(p) + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified fixture passes, two failed unattended-replenishment runs, unchanged runtime and {len(files)} evidence checksums")
