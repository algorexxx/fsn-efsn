import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
target = workspace / "tmp/bootstrap-cache-before"
target.mkdir(parents=True, exist_ok=True)
identities = json.loads((evidence / "initial-live-identities.json").read_text(encoding="utf-8"))
linux_workspace = "/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/"
replacement = {}
for name in ["p2p/discover/table.go", "p2p/discover/database.go"]:
    original = subprocess.check_output(["git", "show", "d7fa207:" + name], cwd=workspace).decode("utf-8").replace("\r\n", "\n")
    if name.endswith("table.go"):
        current = (workspace / name).read_text(encoding="utf-8")
        start = "func (tab *Table) loadSeedNodes() {"
        original_function = start + original.split(start, 1)[1].split("\n}\n", 1)[0] + "\n}\n"
        current_function = start + current.split(start, 1)[1].split("\n}\n", 1)[0] + "\n}\n"
        original = current.replace(current_function, original_function, 1)
    data = original.encode("utf-8")
    blob = subprocess.check_output(["git", "hash-object", "--stdin"], input=data, cwd=workspace).decode().strip()
    assert blob == identities["sources"][name]["git_blob"], name
    path = target / Path(name).name
    path.write_bytes(data)
    replacement[linux_workspace + name] = linux_workspace + path.relative_to(workspace).as_posix()
(target / "overlay.json").write_text(json.dumps({"Replace": replacement}, indent=2) + "\n", encoding="utf-8", newline="\n")
print("Reconstructed and verified both pre-P13 source identities")
