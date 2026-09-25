import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = "a5a6bea5670a2da51a3dd938cc3921b7f57b7731"


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


def leaves(name):
    entries = re.findall(r"^\s*--- (PASS|FAIL|SKIP): (\S+) \(", read(name), re.MULTILINE)
    results = {test: status for status, test in entries}
    return {test: status for test, status in results.items() if not any(other.startswith(test + "/") for other in results)}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


for path in evidence.iterdir():
    if path.is_file() and path.suffix == ".txt":
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))

before = leaves("before-race.txt")
after = leaves("after-race.txt")
assert sum(status == "FAIL" for status in before.values()) == 23
assert sum(status == "PASS" for status in before.values()) == 8
assert before.keys() == after.keys()
assert sum(status == "PASS" for status in after.values()) == 31
assert after["TestRestartPeerAddressLive"] == "SKIP"
for mode, expected in [("before", "1"), ("live-before", "1"), ("after", "0"), ("live-after", "0"), ("regressions", "0"), ("broad", "1")]:
    assert read(mode + "-exit.txt").strip() == expected, mode
    assert "WARNING: DATA RACE" not in read(mode + "-race.txt"), mode
assert leaves("live-before-race.txt") == {"TestRestartPeerAddressLive": "FAIL"}
assert leaves("live-after-race.txt") == {"TestRestartPeerAddressLive": "PASS"}
assert "old reservation released" in read("live-after-race.txt")
assert len(re.findall(r"^ok\s+", read("regressions-race.txt"), re.MULTILINE)) == 3
assert "--- FAIL:" not in read("regressions-race.txt")
known_failures = {"TestParseNode", "TestForwardCompatibility", "TestProtocolHandshake"}
assert set(re.findall(r"^--- FAIL: (\w+)", read("broad-race.txt"), re.MULTILINE)) == known_failures
windows = leaves("windows-tests.txt")
assert len(windows) == 31 and set(windows.values()) == {"PASS"}
assert read("windows-tests.txt").rstrip().endswith("\nPASS")
dns = leaves("dns-race.txt")
assert len(dns) == 6 and set(dns.values()) == {"PASS"}
assert read("dns-race.txt").rstrip().endswith("\nPASS")
assert "WARNING: DATA RACE" not in read("dns-race.txt")
for name in ["efsn-build.txt", "dns-build.txt", "windows-build.txt"]:
    assert read(name) == "", name
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", baseline], cwd=workspace).decode().splitlines()
assert [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")] == ["p2p/discover/table.go"]
names = ["p2p/discover/table.go", "p2p/discover/restart_address_test.go", "p2p/discover/restart_address_linux_test.go", "tests/restart/bootstrap_dns_linux_test.go", "tests/restart/discovery_linux_test.go"]
identities = {
    "baseline": baseline,
    "baseline_table_blob": subprocess.check_output(["git", "rev-parse", baseline + ":p2p/discover/table.go"], cwd=workspace).decode().strip(),
    "sources": {name: {"git_blob": subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(), "sha256_raw": digest(workspace / name)} for name in names},
    "binaries": {name: digest(workspace / name) for name in ["tmp/peer-addresses-efsn", "tmp/peer-addresses-dns-tests", "tmp/peer-addresses-windows-tests.exe"]},
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
summary = {"baseline_failed_cases": 23, "baseline_control_passes": 8, "corrected_deterministic_passes": 31, "windows_passes": 31, "live_udp_before": "FAIL: stale old-subnet reservation", "live_udp_after": "PASS", "dns_live_leaf_passes": 6, "broader_known_failures": sorted(known_failures), "runtime_diff": "+63/-23 in p2p/discover/table.go", "scope": "Local discovery bookkeeping; no consensus, tickets, real keys or chain database work; public deployment not demonstrated"}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(p) + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified 23 baseline failures, 31 corrected Linux/Windows cases, live UDP/DNS checks and three known broad failures; checksummed {len(files)} evidence files")
