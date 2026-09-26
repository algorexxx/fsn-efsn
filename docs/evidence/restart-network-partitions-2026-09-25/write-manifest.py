import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = "27b11869e7835e43c1b3dd6ac98fe80a1efb5430"


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def leaves(name):
    data = read(name)
    assert "WARNING: DATA RACE" not in data, name
    entries = re.findall(r"^\s*--- (PASS|FAIL|SKIP): (\S+) \(", data, re.MULTILINE)
    return [(status, test) for status, test in entries if not any(other.startswith(test + "/") for _, other in entries)]


def expect(name, count, status):
    results = leaves(name)
    assert len(results) == count and {value for value, _ in results} == {status}, (name, results)
    return results


for name in ["build.txt", "final-build.txt", "trace-build.txt", "corrected-build.txt", "windows-build.txt"]:
    assert read(name) == "", name
for name in ["live-exit.txt", "final-live-exit.txt", "self-baseline-exit.txt", "corrected-live-before-exit.txt", "corrected-broad-exit.txt"]:
    assert read(name).strip() == "1", name
for name in ["trace-live-exit.txt", "trace-repeat-exit.txt", "corrected-unit-exit.txt", "corrected-live-after-exit.txt", "corrected-partitions-exit.txt", "corrected-repeat-exit.txt", "windows-unit-exit.txt"]:
    assert read(name).strip() == "0", name
assert baseline in read("environment.txt")
initial = leaves("live-race.txt")
ordinary = leaves("final-live-race.txt")
assert len(initial) == 5 and [test.rsplit("/", 1)[-1] for status, test in initial if status == "FAIL"] == ["dynamic_peers_and_seed_recover", "fresh_dns_contact_udp_blocked"]
assert len(ordinary) == 5 and [test.rsplit("/", 1)[-1] for status, test in ordinary if status == "FAIL"] == ["fresh_dns_contact_udp_blocked"]
assert "SKIP" not in {status for status, _ in initial + ordinary}
expect("trace-live-race.txt", 1, "PASS")
expect("trace-repeat-race.txt", 3, "PASS")
expect("self-baseline-race.txt", 4, "FAIL")
expect("corrected-live-before-race.txt", 1, "FAIL")
expect("corrected-unit-race.txt", 4, "PASS")
expect("corrected-live-after-race.txt", 1, "PASS")
expect("windows-unit.txt", 4, "PASS")
corrected = expect("corrected-partitions-race.txt", 5, "PASS")
expect("corrected-repeat-race.txt", 3, "PASS")
known_failures = {"TestParseNode", "TestForwardCompatibility", "TestProtocolHandshake"}
broad = leaves("corrected-broad-race.txt")
assert {test for status, test in broad if status == "FAIL"} == known_failures
previous_broad = (evidence.parent / "restart-peer-addresses-2026-09-25/broad-race.txt").read_text(encoding="utf-8-sig")
assert set(re.findall(r"^--- FAIL: (\S+) \(", previous_broad, re.MULTILINE)) == known_failures
assert "WARNING: DATA RACE" not in previous_broad
drops = [int(value) for value in re.findall(r"healed partition; netem dropped=(\d+)", read("corrected-partitions-race.txt"))]
assert len(drops) == 5 and all(value > 0 for value in drops), drops
repeat_drops = [int(value) for value in re.findall(r"healed partition; netem dropped=(\d+)", read("corrected-repeat-race.txt"))]
assert len(repeat_drops) == 3 and all(value > 0 for value in repeat_drops)
for event in ["both original protocol connections survived", "reverse-direction authenticated message 75 arrived", "messages 76/77 without AddPeer, manual disconnect or restart", "no static peers, seed TCP service, AddPeer, manual disconnect or restart", "but fresh client stayed peerless while seed UDP was blocked", "authenticated message 82 verified without static peer, seed TCP service or restart"]:
    assert event in read("corrected-partitions-race.txt"), event
initial_fixture = read("initial-fixture.go.txt")
inbound_only = "p2p.Config{NoDial: true, BootstrapNodes: []*discover.Node{contact}}"
assert initial_fixture.count(inbound_only) == 2
assert initial_fixture.replace(inbound_only, "p2p.Config{BootstrapNodes: []*discover.Node{contact}}") == (workspace / "tests/restart/network_partition_linux_test.go").read_text(encoding="utf-8")
source_before = subprocess.check_output(["git", "show", baseline + ":p2p/discover/table.go"], cwd=workspace).decode()
assert source_before == read("baseline-table.go.txt")
source_after = (workspace / "p2p/discover/table.go").read_text(encoding="utf-8")
signature = "func (tab *Table) add(n *Node) {\n"
guard = "\tif n.ID == tab.self.ID {\n\t\treturn\n\t}\n"
assert source_after == source_before.replace(signature, signature + guard, 1)
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", baseline], cwd=workspace).decode().splitlines()
assert [name for name in changed if name.endswith(".go") and not name.endswith("_test.go")] == ["p2p/discover/table.go"]
names = ["p2p/discover/restart_self_test.go", "p2p/discover/restart_self_linux_test.go", "p2p/discover/restart_address_linux_test.go", "p2p/discover/restart_cache_test.go", "tests/restart/network_partition_linux_test.go", "tests/restart/discovery_linux_test.go", "tests/restart/bootstrap_dns_linux_test.go", "p2p/server.go", "p2p/peer.go", "p2p/rlpx.go", "p2p/dial.go", "p2p/discover/bootstrap.go", "p2p/discover/table.go", "p2p/discover/udp.go", "p2p/discover/database.go"]
identities = {
    "baseline": baseline,
    "runtime_change": "P15: three lines at Table.add rejecting the local node ID",
    "sources": {name: {"git_blob": subprocess.check_output(["git", "-c", "core.safecrlf=false", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(), "sha256_raw": digest(workspace / name)} for name in names},
    "binaries": {name: digest(workspace / name) for name in ["tmp/network-partition-tests", "tmp/network-partition-final-tests", "tmp/network-partition-trace-tests", "tmp/network-partition-corrected-tests", "tmp/network-self-windows-tests.exe"]},
    "initial_fixture_sha256": digest(evidence / "initial-fixture.go.txt"),
    "trace_fixture_sha256": digest(evidence / "trace-fixture.go.txt"),
    "binary_scope": "Initial/ordinary-dialing/trace executables use the P1-P14 baseline; corrected and Windows executables add only the three-line P15 runtime guard. Trace overlay only enables test logging. Before-fix signed-UDP test uses the retained baseline table overlay.",
}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
summary = {
    "result": "Focused P15 before/after and corrected partition cases pass; three inherited broad-suite failures remain",
    "deterministic_before_failures": 4,
    "deterministic_after_linux_race_passes": 4,
    "deterministic_after_native_windows_passes": 4,
    "signed_udp_before_failures": 1,
    "signed_udp_after_race_passes": 1,
    "corrected_partition_leaf_passes": len(corrected),
    "corrected_udp_recovery_repeat_passes": 3,
    "kernel_dropped_packets_in_test_order": drops,
    "initial_inbound_only_results": initial,
    "baseline_ordinary_dialing_results": ordinary,
    "baseline_trace_passes": 4,
    "known_broad_suite_failures": sorted(known_failures),
    "runtime_added_lines": 3,
    "permanent_patch_inventory": "P1-P15",
    "limitations": "Isolated IPv4 networking with fixed endpoints; no chain mining/import, production wallets, public routing, real NAT, prolonged or repeated mining partitions, native Windows packet-loss execution or proof of prompt inbound-only recovery",
}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(p) + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified P15's exact three-line guard, baseline failures, corrected cases and known broad failures; checksummed {len(files)} evidence files")
