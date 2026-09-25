from pathlib import Path
import hashlib
import json
import subprocess

directory = Path(__file__).resolve().parent
workspace = directory.parents[2]


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        while data := source.read(1024 * 1024):
            checksum.update(data)
    return checksum.hexdigest()


for name in ["windows-regression.txt", "windows-full-state.txt",
             "linux-regression-race.txt", "linux-full-state-race.txt"]:
    lines = (directory / name).read_text(encoding="utf-8").splitlines()
    assert "PASS" in lines, name
    assert not any("--- FAIL:" in line or "WARNING: DATA RACE" in line or "--- SKIP:" in line for line in lines), name
    for stage in range(1, 4):
        assert any(f"stage={stage}: actual review/prepare/init/sign/export" in line for line in lines), (name, stage)

prior = workspace / "docs/evidence/restart-operator-2026-09-25/identities.json"
prior_identity = json.loads(prior.read_text(encoding="utf-8"))
commands = ["tmp/fsn-recovery-operator.exe", "tmp/fsn-recovery-operator-linux"]
for name in commands:
    assert digest(workspace / name) == prior_identity["binary_sha256"][name], name

manifest = workspace / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS"
assert digest(manifest) == "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf"
source = workspace / "tmp/preserved-head-state"
entries = manifest.read_text(encoding="utf-8").splitlines()
assert len(entries) == 230 and sum(p.is_file() for p in source.rglob("*")) == 230
for line in entries:
    checksum, name = line.split("  ", 1)
    assert digest(source / name) == checksum, name

roots = {platform: workspace / f"tmp/full-state-operator-{platform}-2026-09-25"
         for platform in ["windows", "linux"]}
previous = workspace / "docs/evidence/restart-full-state-offline-2026-09-25/artifacts"
references = [f"step-{stage}.json" for stage in range(1, 4)]
references += [f"block-{stage:02d}.{extension}" for stage in range(1, 4) for extension in ["json", "rlp"]]
references += ["reference/fixture.json", "reference/handover.json"]
for name in references:
    data = (previous / name).read_bytes()
    for root in roots.values():
        assert (root / name).read_bytes() == data, name

artifacts = {}
for stage in range(1, 4):
    for suffix in ["plan.json", "purchase.rlp", "report.json", "block.rlp"]:
        name = f"operator-{stage}-{suffix}"
        data = (roots["windows"] / name).read_bytes()
        assert data == (roots["linux"] / name).read_bytes(), name
        artifacts["shared/" + name] = data
    for platform, root in roots.items():
        approval = root / f"operator-{stage}-approval.json"
        artifacts[platform + "/" + approval.name] = approval.read_bytes()
        decoded = json.loads(approval.read_text(encoding="utf-8"))
        command = commands[0 if platform == "windows" else 1]
        assert decoded["Policy"]["ExecutableSHA256"] == "0x" + digest(workspace / command), approval
        assert (root / f"operator-{stage}-after-import.rlp").read_bytes() == artifacts[f"shared/operator-{stage}-block.rlp"]
        assert artifacts[f"shared/operator-{stage}-block.rlp"] == (previous / f"block-{stage:02d}.rlp").read_bytes()

sources = ["tests/restart/recovery_operator_test.go", "tests/restart/full_state_operator_test.go"]
binaries = commands + ["tmp/full-state-operator-windows-tests.exe", "tmp/full-state-operator-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "04a676c"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection; GOMAXPROCS=2; offline modules; Linux test/command/import processes network isolated",
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "compact_source_manifest_sha256": digest(manifest),
    "source_files_verified_unchanged_after_tests": len(entries),
    "copies_per_platform": 3,
    "bytes_per_initial_copy": 528817080,
    "prior_byte_identical_reference_artifacts": {str((previous / name).relative_to(workspace)).replace("\\", "/"): digest(previous / name) for name in references},
    "complete_state_command_blocks_per_platform": 3,
    "separate_import_and_cold_processes_per_platform": 12,
    "scope": "Same previously reviewed operator executables; complete preserved account state with explicit public scalar 1/2 substitutions; exact command-produced blocks, complete changed-account ledgers and per-owner temporal accounting. No real key, original 117 GB database, W: data, replay checkpoint or public peer opened. No new production code or additional forced crash cuts; not power-loss, full historical replay or independent implementation verification."
}
for name, data in artifacts.items():
    target = directory / "artifacts" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(data)
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.relative_to(directory).as_posix()}\n")
print(f"PASS: {len(files)} evidence files; 18 command artifacts; 11 prior references identical; 230 source files unchanged")
