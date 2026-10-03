import hashlib
import json
from pathlib import Path
import sys

workspace = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(workspace / "tests/restart"))
from snapshot_package import inventory

files = inventory(Path(sys.argv[1]))
encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
result = {
    "files": len(files),
    "bytes": sum(item["size"] for item in files),
    "names_sizes_mtimes_sha256": hashlib.sha256(encoded).hexdigest(),
}
with Path(sys.argv[2]).open("x", encoding="utf-8") as output:
    output.write(json.dumps(result, indent=2) + "\n")
