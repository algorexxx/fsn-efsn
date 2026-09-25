import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=workspace).decode("utf-8").replace("\r\n", "\n").strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


baseline = git("rev-parse", "31433ca")
production = [name for name in git("diff", "--name-only", baseline, "--", "*.go").splitlines() if not name.endswith("_test.go")]
assert production == ["p2p/discover/table.go", "p2p/discover/udp.go"], production
assert git("diff", "--numstat", baseline, "--", *production) == "1\t0\tp2p/discover/table.go\n5\t1\tp2p/discover/udp.go"
for name, function_start in [("p2p/discover/table.go", "func (b *bucket) bump(n *Node) bool {"), ("p2p/discover/udp.go", "func (t *udp) findnode(")]:
    upstream_function = git("show", "c5f0174:" + name).split(function_start)[1].split("\n}\n")[0]
    baseline_function = git("show", baseline + ":" + name).split(function_start)[1].split("\n}\n")[0]
    assert upstream_function == baseline_function, name

results = {}
for name in ["baseline-persistence-race.txt", "current-race.txt"]:
    data = (evidence / name).read_text(encoding="utf-8")
    assert data.rstrip().endswith("\nPASS"), name
    assert "WARNING: DATA RACE" not in data and "--- FAIL:" not in data, name
    for mode in ["learn_short", "short_cold", "learn_mature", "mature_cold", "fresh_cold"]:
        assert f"mode={mode} pid=" in data, (name, mode)
    pids = re.findall(r"mode=\w+ pid=(\d+)", data)
    assert len(set(pids)) == 5, name
    assert data.count("bootstrap=0 static=0") == 3, name
    for event in ["340-second real-time peer maturation complete", "read-only cold inspection verified exact community endpoint", "community outbound dialing disabled", "short-lived child had pong metadata but no saved endpoint", "fresh node with no saved contacts and no seeds remained disconnected"]:
        assert event in data, (name, event)
    duration = re.findall(r"^--- PASS: TestRestartDiscoveryRehearsal \(([^)]+)\)", data, re.MULTILINE)
    assert len(duration) == 1, name
    results[name] = {"duration": duration[0], "separate_child_processes": 5, "result": "PASS with race detection"}

current = (evidence / "current-race.txt").read_text(encoding="utf-8")
for case in ["dns_parse_move_and_multiple_answers", "cli_bootstrap_failures", "seed_outage_and_static_recovery", "persisted_peers_after_seed_shutdown"]:
    assert len(re.findall(r"^    --- PASS: TestRestartDiscoveryRehearsal/" + case + r" \(", current, re.MULTILINE)) == 1
assert len(re.findall(r"^        --- PASS: TestRestartDiscoveryRehearsal/cli_bootstrap_failures/", current, re.MULTILINE)) == 8
before = (evidence / "boundaries-baseline.txt").read_text(encoding="utf-8")
assert re.findall(r"^--- FAIL: (\w+)", before, re.MULTILINE) == ["TestRestartPeerRefreshPreservesMaturation"]
assert "one-minute peer was prematurely persisted after refresh" in before
after = (evidence / "boundaries-current.txt").read_text(encoding="utf-8")
assert len(re.findall(r"^--- PASS: TestRestartPeer", after, re.MULTILINE)) == 3
assert "--- FAIL:" not in after and "WARNING: DATA RACE" not in after
timestamp_only = (evidence / "timestamp-only-race.txt").read_text(encoding="utf-8")
assert "340-second real-time peer maturation complete" in timestamp_only
assert "leveldb: not found" in timestamp_only
assert "--- FAIL: TestRestartDiscoveryRehearsal/persisted_peers_after_seed_shutdown" in timestamp_only
sparse_before = (evidence / "sparse-baseline.txt").read_text(encoding="utf-8")
assert sparse_before.count("err=RPC timeout; want neighbors=") == 2
assert "valid sparse reply penalized responding peer: failures=1" in sparse_before
sparse_after = (evidence / "sparse-current.txt").read_text(encoding="utf-8")
assert len(re.findall(r"^    --- PASS: TestRestartSparseFindnodeReplies/", sparse_after, re.MULTILINE)) == 4
assert "--- PASS: TestRestartSparseReplyDoesNotPenalizePeer" in sparse_after
assert "--- FAIL:" not in sparse_after and "WARNING: DATA RACE" not in sparse_after
regressions = (evidence / "regressions-race.txt").read_text(encoding="utf-8")
assert re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/p2p/discover\s", regressions, re.MULTILINE)
assert "FAIL" not in regressions and "WARNING: DATA RACE" not in regressions

sources = [
    "p2p/discover/table.go", "p2p/discover/database.go", "p2p/discover/udp.go",
    "p2p/discover/restart_cache_test.go", "p2p/discover/restart_partial_reply_test.go", "tests/restart/discovery_linux_test.go",
    "tests/restart/discovery_persistence_linux_test.go", "p2p/server.go",
    "p2p/discover/node.go", "node/node.go", "node/config.go", "cmd/efsn/config.go",
]
identities = {
    "date": "2026-09-25",
    "baseline": baseline,
    "production_change": "Six added/one removed lines across table.go and udp.go: preserve original addedAt on replacement and accept a collection timeout only with validated nonempty neighbors.",
    "baseline_sources": json.loads((evidence / "baseline-sources.json").read_text(encoding="utf-8")),
    "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": sha256(workspace / name)} for name in sources},
    "binaries": {name: sha256(workspace / name) for name in ["tmp/discovery-cache-linux-tests", "tmp/discovery-cache-timestamp-only-linux-tests", "tmp/discovery-cache-current-linux-tests"]},
    "live_results": results,
    "boundary_results": {"before": "lost timestamp and premature persistence", "after": "three tests pass with race detection"},
    "timestamp_only_result": "FAIL: mature live community endpoint was absent from the closed database; timestamp correction alone is insufficient.",
    "sparse_reply_results": {"before": "valid one/two-neighbor replies return timeout and penalize responder", "after": "five cases pass with race detection, including missing/invalid reply controls"},
    "regressions": "PASS with race detection; full-package legacy failures remain documented in prior evidence",
    "baseline_wrapper": "Test completed with PASS; post-test shell output-tail step failed because its script was edited during execution. Current runner is stable and completed separately.",
    "limits": "Actual loopback peer discovery/RLPx with genuine saved endpoints; no real keys or chain execution. Age tests use synthetic timestamps. DNS-error startup is still unfixed. No full-package green claim.",
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(sha256(path) + "  " + path.name for path in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified eleven current live leaf cases, five child processes per run, three boundary cases, five sparse-reply cases and the two-file +6/-1 production delta; checksummed {len(files)} evidence files.")
