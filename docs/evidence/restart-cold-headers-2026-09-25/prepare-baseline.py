import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
target = workspace / "tmp" / "cold-headers-pre-p9-overlay"
target.mkdir(parents=True, exist_ok=True)
baseline = subprocess.check_output(["git", "rev-parse", "bcbd1ce"], cwd=workspace).decode().strip()
replacement = {}
sources = {}
for name in ["consensus/datong/consensus.go", "core/blockchain.go", "core/headerchain.go"]:
    data = subprocess.check_output(["git", "show", baseline + ":" + name], cwd=workspace)
    destination = target / name.replace("/", "_")
    destination.write_bytes(data)
    replacement[str(workspace / name)] = str(destination)
    sources[name] = {"git_blob": subprocess.check_output(["git", "rev-parse", baseline + ":" + name], cwd=workspace).decode().strip(), "sha256": hashlib.sha256(data).hexdigest()}
overlay = target / "overlay.json"
overlay.write_text(json.dumps({"Replace": replacement}, indent=2) + "\n", encoding="utf-8", newline="\n")
(evidence / "baseline-sources.json").write_text(json.dumps({"baseline": baseline, "scope": "Only the three P9 runtime files are overlaid with pre-P9 bytes; current tests and all other runtime sources retained.", "sources": sources}, indent=2) + "\n", encoding="utf-8", newline="\n")
print(overlay)
