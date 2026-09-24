import hashlib
import json
import pathlib
import shutil

evidence = pathlib.Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / "tmp/preserved-head-state"
manifest = workspace / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS"

def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()

assert digest(manifest) == "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf"
entries = [line.split("  ./", 1) for line in manifest.read_text(encoding="utf-8").splitlines()]
assert len(entries) == 230
assert len([p for p in source.rglob("*") if p.is_file()]) == 230
for expected, relative in entries:
    assert digest(source / relative) == expected, relative

def archive(original, name):
    target = evidence / name
    assert not target.exists(), target
    shutil.copyfile(original, target)
    assert digest(original) == digest(target)

sizes = {}
for role in ("producer", "verifier"):
    target = workspace / f"tmp/full-state-{role}"
    archive(target / "fixture.json", f"{role}-fixture.json")
    archive(target / "cold-verified.json", f"{role}-cold-verified.json")
    files = sorted(p for p in target.rglob("*") if p.is_file())
    (evidence / f"{role}-artifact-SHA256SUMS").write_text(
        "".join(f"{digest(p)}  ./{p.relative_to(target).as_posix()}\n" for p in files), encoding="utf-8")
    sizes[role] = {"files": len(files), "bytes": sum(p.stat().st_size for p in files)}
assert (evidence / "producer-fixture.json").read_bytes() == (evidence / "verifier-fixture.json").read_bytes()
assert (evidence / "producer-cold-verified.json").read_bytes() == (evidence / "verifier-cold-verified.json").read_bytes()
for block in sorted((workspace / "tmp/full-state-bridge").iterdir()):
    archive(block, block.name)
assert (evidence / "accounting.json").read_bytes() == (evidence / "accounting-linux.json").read_bytes()
identities = {}
for path in sorted((workspace / "tests/restart").glob("full_state*test.go")):
    identities[path.relative_to(workspace).as_posix()] = digest(path)
for relative in ("tmp/full-state-tests.exe", "tmp/full-state-final-tests.exe", "tmp/full-state-context-v2-linux-tests", "tmp/full-state-final-linux-tests"):
    identities[relative] = digest(workspace / relative)
(evidence / "final-identities.json").write_text(json.dumps(identities, indent=2)+"\n", encoding="utf-8")
(evidence / "closed-artifacts.json").write_text(json.dumps(sizes, indent=2)+"\n", encoding="utf-8")
(evidence / "source-preserved.txt").write_text("All 230 original state-artifact files still match the preserved manifest after rehearsal.\nProducer/verifier fixture ledgers and cold inventories match exactly.\nWindows/Linux decoded accounting ledgers match byte-for-byte.\n", encoding="utf-8")
print(json.dumps(sizes, indent=2))
