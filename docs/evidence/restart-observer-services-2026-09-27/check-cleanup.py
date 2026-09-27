import json
import os
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-4"
config = json.loads((attempt / "services/ipc-divergence-config.json").read_text(encoding="utf-8"))
paths = [Path(node["Endpoint"]).parent for node in config["Nodes"]]
assert all(path.parent == Path("/tmp") and path.name.startswith("fsn-dense-miner-") for path in paths)
targets = {str(workspace / "tmp/restart-observer-services" / name)
           for name in ("services-tests", "fsn-observe")}
remaining = []
for process in Path("/proc").iterdir():
    if not process.name.isdecimal():
        continue
    try:
        executable = os.readlink(process / "exe")
    except (FileNotFoundError, ProcessLookupError):
        continue
    if executable in targets:
        remaining.append(int(process.name))
result = {"TemporaryNodeDirectories": [str(path) for path in paths],
          "TemporaryNodeDirectoriesRemoved": all(not path.exists() for path in paths),
          "ResidualProcesses": remaining}
(attempt / "cleanup.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
assert result["TemporaryNodeDirectoriesRemoved"] and not remaining, result
print(json.dumps(result, indent=2))
