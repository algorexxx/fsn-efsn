import json
import subprocess
import tomllib
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
scratch = workspace / "tmp/network-profile-config"
scratch.mkdir(parents=True, exist_ok=True)
linux_workspace = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
binary = linux_workspace + "tmp/peer-addresses-efsn"
seed = "enode://79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8@seed.restart.invalid:40408"
profile = workspace / "docs/restart-network-profile.toml"
results = []


def linux(path):
    return linux_workspace + path.relative_to(workspace).as_posix()


def run(name, flags, success=True):
    args = ["--datadir", linux(scratch / name), *flags, "dumpconfig"]
    command = ["wsl", "-d", "FusionRehearsal", "-u", "root", "--", "unshare", "--net", "--", "runuser", "-u", "rehearsal", "--", binary, *args]
    process = subprocess.run(command, capture_output=True, timeout=25)
    output = process.stdout.decode("utf-8").replace("\r\n", "\n")
    error = process.stderr.decode("utf-8").replace("\r\n", "\n")
    (evidence / (name + ".stdout.txt")).write_text(output, encoding="utf-8", newline="\n")
    (evidence / (name + ".stderr.txt")).write_text(error, encoding="utf-8", newline="\n")
    assert (process.returncode == 0) == success, (name, process.returncode, error, output)
    parsed = tomllib.loads(output) if success else {}
    results.append({"name": name, "arguments": args, "exit": process.returncode, "node": parsed.get("Node"), "sync_mode": parsed.get("Eth", {}).get("SyncMode")})
    print(name + ": " + ("configuration accepted" if success else "expected rejection"), flush=True)
    return parsed


defaults = run("defaults", [])
assert len(defaults["Node"]["P2P"]["BootstrapNodes"]) == 4
assert len(defaults["Node"]["P2P"]["BootstrapNodesV5"]) == 4
assert defaults["Node"]["HTTPHost"] == defaults["Node"]["WSHost"] == ""
assert defaults["Node"]["P2P"].get("DiscoveryV5", False) is False
base = ["--config", linux(profile), "--syncmode", "full", "--bootnodesv4=" + seed, "--bootnodesv5=", "--v5disc=false", "--http=false", "--ws=false"]
for name, port, address in [("backup_profile", 40409, "192.0.2.10"), ("donation_profile", 40408, "192.0.2.10"), ("ipv6_profile", 40408, "2001:db8::10")]:
    config = run(name, base + ["--port", str(port), "--nat", "extip:" + address])
    p2p = config["Node"]["P2P"]
    assert p2p["ListenAddr"] == ":" + str(port)
    assert p2p["BootstrapNodes"] == [seed]
    assert p2p.get("BootstrapNodesV5", []) == [] and not p2p.get("DiscoveryV5", False)
    assert p2p["StaticNodes"] == p2p["TrustedNodes"] == [] and not p2p["NoDiscovery"]
    assert config["Node"]["HTTPHost"] == config["Node"]["WSHost"] == "" and config["Eth"]["SyncMode"] == "full"

run("nat_hostname_rejected", base + ["--nat", "extip:seed.restart.invalid"], success=False)
run("external_ip_dump_reload_rejected", ["--config", linux(evidence / "backup_profile.stdout.txt")], success=False)
none = run("nat_none_dump", ["--bootnodesv4=", "--bootnodesv5=", "--v5disc=false", "--nat", "none", "--syncmode", "full"])
assert "NAT" not in none["Node"]["P2P"] and "BootstrapNodesV5" not in none["Node"]["P2P"]
reload = run("nat_none_dump_reload", ["--config", linux(evidence / "nat_none_dump.stdout.txt")])
assert "NAT" not in defaults["Node"]["P2P"] and "NAT" not in reload["Node"]["P2P"]
assert len(reload["Node"]["P2P"]["BootstrapNodesV5"]) == 4
disabled = run("nodiscover_and_v5", ["--bootnodesv4=", "--bootnodesv5=", "--nat", "none", "--nodiscover", "--v5disc"])
assert disabled["Node"]["P2P"]["NoDiscovery"] is True and disabled["Node"]["P2P"]["DiscoveryV5"] is True
false_flag = run("nodiscover_false", ["--bootnodesv4=", "--bootnodesv5=", "--nat", "none", "--nodiscover=false"])
assert false_flag["Node"]["P2P"]["NoDiscovery"] is True
(evidence / "config-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"Verified {len(results)} actual-command configuration cases; no P2P service or chain database started")
