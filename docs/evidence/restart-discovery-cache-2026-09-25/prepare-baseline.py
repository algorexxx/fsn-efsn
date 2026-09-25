import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
target = workspace / "tmp" / "discovery-cache-baseline-overlay"
target.mkdir(parents=True, exist_ok=True)
baseline = subprocess.check_output(["git", "rev-parse", "31433ca"], cwd=workspace).decode().strip()
linux_workspace = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
replacement = {}
sources = {}
for name in ["p2p/discover/table.go", "p2p/discover/udp.go"]:
    data = subprocess.check_output(["git", "show", baseline + ":" + name], cwd=workspace)
    destination = target / Path(name).name
    destination.write_bytes(data)
    replacement[linux_workspace + name] = linux_workspace + destination.relative_to(workspace).as_posix()
    sources[name] = {"git_blob": subprocess.check_output(["git", "rev-parse", baseline + ":" + name], cwd=workspace).decode().strip(), "sha256": hashlib.sha256(data).hexdigest()}
(target / "overlay.json").write_text(json.dumps({"Replace": replacement}, indent=2) + "\n", encoding="utf-8", newline="\n")
(evidence / "baseline-sources.json").write_text(json.dumps({"baseline": baseline, "scope": "Discovery table.go and udp.go are replaced with pre-P11 sources; P10 initialization ordering remains included.", "sources": sources}, indent=2) + "\n", encoding="utf-8", newline="\n")
print(target / "overlay.json")
