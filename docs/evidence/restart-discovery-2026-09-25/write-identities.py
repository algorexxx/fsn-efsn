import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=workspace).decode("utf-8").strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


baseline = git("rev-parse", "0df4014")
production = [name for name in git("diff", "--name-only", baseline, "--", "*.go").splitlines() if not name.endswith("_test.go")]
assert production == ["p2p/discover/table.go", "p2p/discover/udp.go"], production
for name in production:
    assert git("rev-parse", baseline + ":" + name) == git("rev-parse", "c5f0174:" + name), name
for name in ["p2p/discover/node.go", "p2p/discover/node_test.go", "p2p/discover/udp_test.go", "p2p/rlpx.go", "p2p/rlpx_test.go"]:
    assert git("hash-object", "--path=" + name, name) == git("rev-parse", "c5f0174:" + name), name
assert sorted(git("diff", "--numstat", baseline, "--", *production).splitlines()) == [
    "0\t1\tp2p/discover/table.go", "1\t0\tp2p/discover/udp.go"
]

current = (evidence / "current-race.txt").read_text(encoding="utf-8")
before = (evidence / "baseline-race.txt").read_text(encoding="utf-8")
assert current.rstrip().endswith("\nPASS") and "WARNING: DATA RACE" not in current and "--- FAIL:" not in current
assert before.rstrip().endswith("\nFAIL") and "WARNING: DATA RACE" in before
assert "timed out:" not in before
for case in ["dns_parse_move_and_multiple_answers", "cli_bootstrap_failures", "seed_outage_and_static_recovery"]:
    assert len(re.findall(r"^    --- PASS: TestRestartDiscoveryRehearsal/" + case + r" \(", current, re.MULTILINE)) == 1
for case in ["healthy", "bad_then_good", "good_then_bad", "all_bad", "nodiscover_bad", "empty", "nodiscover_empty", "malformed"]:
    assert len(re.findall(r"^        --- PASS: TestRestartDiscoveryRehearsal/cli_bootstrap_failures/" + case + r" \(", current, re.MULTILINE)) == 1
for log in [current, before]:
    for event in ["two fresh nodes discovered each other through one seed", "existing peers still exchange messages after 25 seconds", "both fresh nodes recovered through a literal-IP static peer"]:
        assert event in log, event
legacy_failures = ["TestForwardCompatibility", "TestParseNode", "TestProtocolHandshake"]
for name in ["package-race.txt", "package-baseline-failures.txt"]:
    data = (evidence / name).read_text(encoding="utf-8")
    assert sorted(re.findall(r"^--- FAIL: (\w+)", data, re.MULTILINE)) == legacy_failures, name
    assert "WARNING: DATA RACE" not in data, name
focused = (evidence / "package-focused-race.txt").read_text(encoding="utf-8")
assert len(re.findall(r"^ok\s+github.com/FusionFoundation/efsn/v5/p2p(?:/discover)?\s", focused, re.MULTILINE)) == 2
assert "FAIL" not in focused and "WARNING: DATA RACE" not in focused

sources = production + [
    "p2p/discover/table_test.go", "tests/restart/discovery_linux_test.go",
    "cmd/utils/flags.go", "p2p/discover/node.go", "p2p/discv5/node.go",
    "p2p/server.go", "p2p/dial.go", "node/api.go", "node/config.go",
    "p2p/discover/node_test.go", "p2p/discover/udp_test.go", "p2p/rlpx.go", "p2p/rlpx_test.go",
]
binaries = ["tmp/discovery-linux-tests", "tmp/discovery-baseline-linux-tests", "tmp/discovery-current-linux-tests"]
identities = {
    "date": "2026-09-25",
    "baseline": baseline,
    "production_change": "Move go tab.loop() after UDP transport initialization; one added and one removed production line.",
    "production_paths": production,
    "baseline_sources": json.loads((evidence / "baseline-sources.json").read_text(encoding="utf-8")),
    "current_sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256_raw": sha256(workspace / name)} for name in sources},
    "binaries": {name: sha256(workspace / name) for name in binaries},
    "results": {
        "current": {"leaf_cases": 10, "duration_seconds": 30.44, "race_detection": "PASS"},
        "baseline": {"duration_seconds": 60.92, "connectivity_assertions": "PASS", "race_detection": "FAIL", "race_reports": before.count("WARNING: DATA RACE")},
        "focused_packages": "PASS with race detection",
        "full_packages": {"status": "FAIL", "preexisting_failures_reproduced": legacy_failures},
    },
    "limits": "Loopback-only UDP/RLPx test protocol, controlled IPv4 DNS and CLI configuration subprocesses. No chain execution, real keys, public networking, persisted-peer cold restart or DNS retry implementation.",
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(sha256(path) + "  " + path.name for path in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified ten passing leaf cases, baseline race and three inherited package failures; checksummed {len(files)} evidence files.")
