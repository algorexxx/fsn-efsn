import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / "tmp/preserved-head-state"
target = workspace / "tmp/full-state-participant-2026-09-26"
manifest = workspace / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS"
expected = "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


assert digest(manifest) == expected
assert not target.exists(), "refusing to reuse or overwrite an existing rehearsal"
entries = [line.split("  ./", 1) for line in manifest.read_text(encoding="utf-8").splitlines()]
assert len(entries) == 230
assert len([p for p in source.rglob("*") if p.is_file()]) == 230
size = sum((source / relative).stat().st_size for _, relative in entries)
assert shutil.disk_usage(workspace).free > 50 * 1024**3 + size * 2
for expected_hash, relative in entries:
    path = (source / relative).resolve()
    assert source.resolve() in path.parents and digest(path) == expected_hash, relative
for role in ["producer", "verifier"]:
    directory = target / role
    directory.mkdir(parents=True)
    for expected_hash, relative in entries:
        destination = directory / relative
        assert directory.resolve() in destination.resolve().parents
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, destination)
        assert digest(destination) == expected_hash, str(destination)
    proof = {"Source": str(source), "ManifestSHA256": expected, "Files": len(entries)}
    for path in [directory / "copy-verified.json", evidence / (role + "-copy-verified.json")]:
        path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8", newline="\n")
report = {"source_files": len(entries), "source_bytes": size, "copies": 2, "copied_bytes": size * 2, "free_bytes_after_copy": shutil.disk_usage(workspace).free}
(evidence / "copy-capacity.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(report))
