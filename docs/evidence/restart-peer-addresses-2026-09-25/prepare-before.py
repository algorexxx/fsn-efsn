import json
import subprocess
from pathlib import Path

workspace = Path(__file__).resolve().parents[3]
target = workspace / "tmp/peer-addresses-before"
target.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(["git", "show", "a5a6bea5670a2da51a3dd938cc3921b7f57b7731:p2p/discover/table.go"], cwd=workspace)
(target / "table.go").write_bytes(source)
linux = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
(target / "overlay.json").write_text(json.dumps({"Replace": {linux + "p2p/discover/table.go": linux + "tmp/peer-addresses-before/table.go"}}, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Prepared unchanged baseline discovery table overlay")
