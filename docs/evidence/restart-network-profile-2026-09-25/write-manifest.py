import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
baseline = "c6ab88e576da531be8c5486df22a4e05a3e39bc1"


def read(name):
    return (evidence / name).read_text(encoding="utf-8-sig")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def check_live(name, count):
    data = read(name)
    entries = re.findall(r"^\s*--- (PASS|FAIL|SKIP): (\S+) \(", data, re.MULTILINE)
    results = {test: status for status, test in entries}
    leaves = {test: status for test, status in results.items() if not any(other.startswith(test + "/") for other in results)}
    assert len(leaves) == count and set(leaves.values()) == {"PASS"}, leaves
    assert "WARNING: DATA RACE" not in data and data.rstrip().endswith("\nPASS")
    return leaves


for name in ["build.txt", "final-build.txt"]:
    assert read(name) == ""
for name in ["live-exit.txt", "final-live-exit.txt"]:
    assert read(name).strip() == "0"
check_live("live-race.txt", 13)
leaves = check_live("final-live-race.txt", 17)
for event in ["without static or bootstrap TCP fallback", "input config contains zero static/trusted entries; effective server loads 1", "effective NAT adapter present=true", "effective NAT adapter present=false", "restart refreshed it with unchanged identity", "running status does not establish public reachability"]:
    assert event in read("final-live-race.txt"), event
configs = json.loads(read("config-results.json"))
assert len(configs) == 10
assert {case["name"] for case in configs if case["exit"] != 0} == {"nat_hostname_rejected", "external_ip_dump_reload_rejected"}
assert "cannot unmarshal TOML array into nat.Interface" in read("external_ip_dump_reload_rejected.stderr.txt")
assert "invalid IP address" in read("nat_hostname_rejected.stderr.txt")
for case in configs:
    if case["name"] == "backup_profile":
        assert case["node"]["P2P"]["ListenAddr"] == ":40409"
    if case["name"] == "donation_profile":
        assert case["node"]["P2P"]["ListenAddr"] == ":40408"
inventory = json.loads(read("endpoint-inventory.json"))
assert len(inventory["matches"]) == 52 and len(inventory["source_sha256"]) == 22 and inventory["files_scanned"] == 766
for name, expected in inventory["source_sha256"].items():
    assert digest(workspace / name) == expected, name
changed = subprocess.check_output(["git", "-c", "core.safecrlf=false", "diff", "--name-only", baseline], cwd=workspace).decode().splitlines()
assert not any(name.endswith(".go") and not name.endswith("_test.go") for name in changed)
previous = json.loads((evidence.parent / "restart-peer-addresses-2026-09-25/identities.json").read_text(encoding="utf-8"))
assert digest(workspace / "tmp/peer-addresses-efsn") == previous["binaries"]["tmp/peer-addresses-efsn"]
names = ["tests/restart/discovery_linux_test.go", "tests/restart/bootstrap_dns_linux_test.go", "tests/restart/network_profile_linux_test.go", "tests/restart/network_config_test.go", "docs/restart-network-profile.toml", "p2p/server.go", "p2p/nat/nat.go", "node/config.go", "node/node.go", "node/defaults.go", "cmd/utils/flags.go", "cmd/efsn/config.go", "params/bootnodes.go"]
identities = {"baseline": baseline, "node_runtime_changes": [], "sources": {name: {"git_blob": subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(), "sha256_raw": digest(workspace / name)} for name in names}, "binaries": {name: digest(workspace / name) for name in ["tmp/peer-addresses-efsn", "tmp/network-profile-tests", "tmp/network-profile-final-tests"]}, "binary_scope": "Reused efsn verified against P14 evidence; initial test executable covers 13 cases; final executable adds the four NetworkConfigInputs cases, with all 17 rerun"}
(evidence / "identities.json").write_text(json.dumps(identities, indent=2) + "\n", encoding="utf-8", newline="\n")
summary = {"result": "PASS: isolated Linux race rehearsals and expected actual-command outcomes", "final_live_leaf_passes": len(leaves), "actual_command_cases": 10, "expected_rejections": 2, "endpoint_references": 52, "node_runtime_changes": 0, "permanent_patch_inventory": "P1-P14 unchanged", "limitations": "Loopback networking and synthetic NAT; no real router, public routing, partition, mining, chain database, deployment or production wallet work; no full-suite rerun"}
(evidence / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("\n".join(digest(p) + "  " + p.name for p in files) + "\n", encoding="utf-8", newline="\n")
print(f"Verified 17 race cases, 10 command cases, 52 endpoint references, unchanged runtime and reused node binary; checksummed {len(files)} files")
