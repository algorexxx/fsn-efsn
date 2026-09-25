import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=workspace).decode().split("\0")
patterns = {
    "foundation_hostname": re.compile(r"\b(?:[a-z0-9-]+\.)*(?:fusionnetwork\.(?:io|org)|fusion\.org)\b", re.I),
    "old_image_namespace": re.compile(r"\bfusionnetwork/[a-z0-9-]+", re.I),
    "original_repository_url": re.compile(r"https://(?:raw\.githubusercontent\.com|github\.com)/fusionfoundation/[^\s\"'<>`)]+", re.I),
    "literal_bootstrap": re.compile(r"enode://[0-9a-f]+@([0-9.]+:[0-9]+)", re.I),
}
matches = []
sources = {}
scanned = []
for name in paths:
    if not name or name.startswith(("docs/", "vendor/", "tests/")) or name.endswith(("_test.go", ".test.sh", ".sum")):
        continue
    path = workspace / name
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        continue
    if path.suffix not in {".go", ".sh", ".md", ".yml", ".yaml", ".toml", ".json"} and not path.name.startswith("Dockerfile"):
        continue
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    scanned.append(name)
    for number, line in enumerate(text.splitlines(), 1):
        for kind, pattern in patterns.items():
            for match in pattern.finditer(line):
                value = match.group(1) if kind == "literal_bootstrap" else match.group(0)
                matches.append({"file": name, "line": number, "kind": kind, "value": value})
                sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
result = {"baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace).decode().strip(), "scope": "Tracked source/install/reference files under 1 MiB; excludes investigation docs/evidence, vendor, tests and dependency checksums; values only, no credentials; no endpoint contacted", "files_scanned": len(scanned), "matches": matches, "source_sha256": sources}
(evidence / "endpoint-inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"Inventoried {len(matches)} references in {len(sources)} files across {len(scanned)} scanned files; no network access")
