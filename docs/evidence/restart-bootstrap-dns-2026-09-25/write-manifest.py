import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


live = read("verified-race.txt")
assert live.rstrip().endswith("\nPASS")
assert "WARNING: DATA RACE" not in live and "--- FAIL:" not in live
durations = dict(re.findall(r"^--- PASS: (TestRestart\w+) \(([^)]+)\)", live, re.MULTILINE))
assert set(durations) == {"TestRestartBootstrapDNSRehearsal", "TestRestartDiscoveryRehearsal"}
for leaf in ["toml_operator_command/unresolved", "toml_operator_command/cli_empty_override", "toml_operator_command/malformed", "outage_recovery_udp_only_and_move", "restricted_answers", "shutdown_during_blocked_lookup"]:
    assert re.search(r"^ +--- PASS: TestRestartBootstrapDNSRehearsal/" + leaf + r" \(", live, re.MULTILINE), leaf
assert len(re.findall(r"^        --- PASS: TestRestartDiscoveryRehearsal/cli_bootstrap_failures/", live, re.MULTILINE)) == 8
for event in ["340-second real-time peer maturation complete", "read-only cold inspection verified exact community endpoint", "despite NXDOMAIN bootstrap", "community outbound dialing disabled", "fresh node with no saved or usable configured contacts remained disconnected", "shutdown cancelled an in-flight nonresponding DNS lookup"]:
    assert event in live, event
assert len(set(re.findall(r"mode=\w+ pid=(\d+)", live))) == 5
assert "--- FAIL: TestRestartBootstrapRefreshKeepsResolvedAddress" in read("cache-before.txt")
assert "--- PASS: TestRestartBootstrapRefreshKeepsResolvedAddress" in read("cache-current.txt")
units = read("units-race.txt")
assert len(re.findall(r"^ok\s+", units, re.MULTILINE)) == 3
assert "FAIL" not in units and "WARNING: DATA RACE" not in units
broad = read("broad-race.txt")
assert set(re.findall(r"^--- FAIL: (\w+)", broad, re.MULTILINE)) == {"TestParseNode", "TestForwardCompatibility", "TestProtocolHandshake"}
assert "WARNING: DATA RACE" not in broad and read("broad-exit.txt").strip() == "1"
windows = read("windows-tests.txt")
assert windows.rstrip().endswith("\nPASS") and "--- FAIL:" not in windows
current = json.loads(read("current-identities.json"))
previous = json.loads(read("pre-fixture-identities.json"))
for name, identity in current["sources"].items():
    blob = subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip()
    assert blob == identity["git_blob"], name
    if not name.endswith("_test.go"):
        assert identity == previous["sources"][name], name
assert current["binaries"]["tmp/bootstrap-dns-final-efsn"] == previous["binaries"]["tmp/bootstrap-dns-final-efsn"]
summary = {"result": "PASS: corrected combined Linux rehearsal, focused Linux race regressions and native Windows discovery checks", "live_durations": durations, "live_leaf_cases": 17, "separate_cache_child_processes": 5, "broad_package_failures": ["TestParseNode", "TestForwardCompatibility", "TestProtocolHandshake"], "fixture_race": "Retained in full-race.txt and final-race.txt; corrected explicit resolver in verified-race.txt; node runtime sources unchanged by fixture correction", "limitations": "Loopback-only live tests; public subnet accounting and stale revalidation remain open; no real keys, chain execution or deployment"}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified final live/Windows/focused checks, three known broader failures, unchanged runtime across fixture correction; checksummed {len(files)} evidence files")
