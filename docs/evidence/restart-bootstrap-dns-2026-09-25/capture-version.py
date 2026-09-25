import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
label = sys.argv[1]
assert label in {"initial-live", "current"}
names = ["cmd/utils/flags.go", "p2p/server.go", "p2p/discover/node.go", "p2p/discover/bootstrap.go", "p2p/discover/table.go", "p2p/discover/database.go", "p2p/discover/udp.go", "tests/restart/bootstrap_dns_linux_test.go", "tests/restart/discovery_linux_test.go", "tests/restart/discovery_persistence_linux_test.go"]
if label == "current":
    names += ["p2p/discover/bootstrap_test.go", "p2p/discover/bootstrap_deadline_test.go", "p2p/discover/bootstrap_cache_test.go"]

def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()

binaries = ["tmp/bootstrap-dns-final-efsn", "tmp/bootstrap-dns-verified-tests"] if label == "current" else ["tmp/bootstrap-dns-efsn", "tmp/bootstrap-dns-tests"]
if label == "current":
    binaries += ["tmp/bootstrap-dns-windows-tests.exe"]
result = {"baseline": subprocess.check_output(["git", "rev-parse", "d7fa207"], cwd=workspace).decode().strip(), "label": label, "sources": {name: {"git_blob": subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace).decode().strip(), "sha256_raw": digest(workspace / name)} for name in names}, "binaries": {name: digest(workspace / name) for name in binaries}}
(evidence / (label + "-identities.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Captured " + label + " source and binary identities")
