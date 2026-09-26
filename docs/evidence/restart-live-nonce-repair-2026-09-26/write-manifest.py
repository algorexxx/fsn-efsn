import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", "-c", "core.safecrlf=false", *args], cwd=workspace).decode().strip()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


data = (evidence / "live-initial-race.txt").read_text(encoding="utf-8")
assert (evidence / "live-initial-exit.txt").read_text(encoding="utf-8").strip() == "0"
assert (evidence / "build.txt").read_bytes() == b""
assert "--- PASS: TestRestartNodeRehearsal/continuous_partition_nonce_repair" in data
assert not any(value in data for value in ["--- FAIL:", "--- SKIP:", "WARNING: DATA RACE"])
gap = re.search(r"stable gap node=(\d+) canonical=(\d+) saved=(\d+) hash=(0x[0-9a-f]+) common=(\d+) after-heal=(\S+)", data)
assert gap and int(gap[3]) > int(gap[2])
originals = re.findall(r"original included node=(\d+) nonce=(\d+) hash=(0x[0-9a-f]+) block=(\d+) (0x[0-9a-f]+)", data)
assert [int(item[1]) for item in originals] == list(range(int(gap[2]), int(gap[3])))
assert all(item[0] == gap[1] for item in originals)
saved = re.search(r"exact saved intent included nonce=(\d+) hash=(0x[0-9a-f]+) block=(\d+)", data)
assert saved and saved[1] == gap[3] and saved[2] == gap[4]
successors = int(re.search(r"resumed with (\d+) new automatic successors", data)[1])
assert successors >= 2
tickets = re.findall(r"tickets phase=(\S+) block=(\d+) owner=(\d+) stored=(\d+) valid-next-period=(\d+)", data)
assert {entry[0] for entry in tickets} == {"before-outage", "isolated", "paused-before-repair", "missing-nonce-included", "automatic-successors"}
assert all(int(entry[3]) >= int(entry[4]) > 0 for entry in tickets)
cold = re.findall(r"cold node=(\d+) nonce=(\d+) saved-bytes=(\d+) canonical receipts=(\d+)", data)
assert len(cold) == 2 and {entry[0] for entry in cold} == {"1", "2"}
assert all(int(entry[3]) == len(originals) + 1 + successors for entry in cold)
final = re.search(r"live nonce repair passed: final=(\d+) (0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+) originals=(\d+) automatic-successors=(\d+)", data)
assert final and int(final[5]) == len(originals) and int(final[6]) == successors
drops = re.findall(r"healed partition; netem dropped=(\d+)", data)
assert len(drops) == 1 and int(drops[0]) > 0
baseline = git("rev-parse", "e0a002b")
assert baseline in (evidence / "environment.txt").read_text(encoding="utf-8")
changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")]
source = (workspace / "tests/restart/continuous_repair_linux_test.go").read_text(encoding="utf-8")
assert source.count("connectRehearsalPeer(") == 1
assert "lab_sync" not in source and "syncRecoveryNode(" not in source and "lab_holdWorker" not in source
assert source.index("stopPeerAutoMiner(") > source.index("resumed with %d new automatic successors")
names = ["tests/restart/continuous_repair_linux_test.go", "tests/restart/node_rehearsal_linux_test.go", "tests/restart/dense_miner_fixture_linux_test.go", "tests/restart/continuous_partition_linux_test.go", "tests/restart/partition_miners_linux_test.go", "tests/restart/network_partition_linux_test.go", "tests/restart/competing_miners_linux_test.go", "tests/restart/purchase_peer_linux_test.go", "common/ticket.go", "common/fsnparams.go", "consensus/datong/consensus.go", "core/blockchain.go", "core/tx_pool.go", "internal/ethapi/autobuy.go", "internal/ethapi/api.go", "internal/ethapi/api_fsn.go", "eth/api_backend.go", "go.mod", "go.sum"]
binary = digest(workspace / "tmp/live-nonce-repair-tests")
assert binary == (evidence / "binary.sha256").read_text(encoding="utf-8").split()[0]
identities = {"baseline": baseline, "runtime_changes": 0, "patch_inventory": "P1-P15", "binary_sha256": binary, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": digest(workspace / name)} for name in names}}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
result = {"result": "PASS: explicit sequential nonce repair during uninterrupted mining", "test_seconds": float(re.search(r"continuous_partition_nonce_repair \(([0-9.]+)s\)", data)[1]), "kernel_drops": int(drops[0]), "gap": {"node": int(gap[1]), "canonical_nonce": int(gap[2]), "saved_nonce": int(gap[3]), "saved_hash": gap[4], "common_block": int(gap[5]), "after_heal": gap[6]}, "originals": [{"nonce": int(item[1]), "hash": item[2], "block": int(item[3]), "block_hash": item[4]} for item in originals], "automatic_successors": successors, "ticket_samples": [{"phase": item[0], "block": int(item[1]), "owner": int(item[2]), "stored": int(item[3]), "valid_next_period": int(item[4])} for item in tickets], "cold_observations": [{"node": int(item[0]), "nonce": int(item[1]), "saved_bytes": int(item[2]), "canonical_receipts": int(item[3])} for item in cold], "final": {"number": int(final[1]), "hash": final[2], "state_root": final[3], "ticket_root": final[4]}, "limits": "One 90-second isolated synthetic devnet outage, generous funding/tickets, preserved original bytes. No automatic repair, production runway, orphan-RPC retrieval, public-network or power-loss claim. Earlier unattended-replenishment tests remain failed."}
(evidence / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(path) + "  " + path.name for path in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified live repair, exact original/saved purchases, {successors} automatic successors, cold receipts, unchanged runtime and {len(files)} evidence checksums")
