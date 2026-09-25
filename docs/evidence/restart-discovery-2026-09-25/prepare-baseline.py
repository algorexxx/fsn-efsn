import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
target = workspace / "tmp" / "discovery-pre-p10-overlay"
target.mkdir(parents=True, exist_ok=True)
baseline = subprocess.check_output(["git", "rev-parse", "0df4014"], cwd=workspace).decode().strip()
replacement = {}
sources = {}
for name in ["p2p/discover/table.go", "p2p/discover/udp.go", "p2p/discover/table_test.go"]:
    data = subprocess.check_output(["git", "show", baseline + ":" + name], cwd=workspace)
    destination = target / name.replace("/", "_")
    destination.write_bytes(data)
    linux_workspace = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
    replacement[linux_workspace + name] = linux_workspace + destination.relative_to(workspace).as_posix()
    sources[name] = {"git_blob": subprocess.check_output(["git", "rev-parse", baseline + ":" + name], cwd=workspace).decode().strip(), "sha256": hashlib.sha256(data).hexdigest()}
(target / "overlay.json").write_text(json.dumps({"Replace": replacement}, indent=2) + "\n", encoding="utf-8", newline="\n")
(evidence / "baseline-sources.json").write_text(json.dumps({"baseline": baseline, "scope": "Restore the two discovery runtime files and their table test constructor call sites to pre-P10 bytes.", "sources": sources}, indent=2) + "\n", encoding="utf-8", newline="\n")
print(target / "overlay.json")
