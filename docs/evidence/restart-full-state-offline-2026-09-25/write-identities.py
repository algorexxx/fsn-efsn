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
    assert "PASS" in lines and not any("--- FAIL:" in line or "WARNING: DATA RACE" in line for line in lines), name

roots = {platform: workspace / f"tmp/full-state-offline-{platform}-2026-09-25"
         for platform in ["windows", "linux"]}
files = [f"step-{stage}.json" for stage in range(1, 4)]
files += [f"block-{stage:02d}.{extension}" for stage in range(1, 4) for extension in ["json", "rlp"]]
files += ["reference/fixture.json", "reference/handover.json"]
for name in files:
    data = (roots["windows"] / name).read_bytes()
    assert data == (roots["linux"] / name).read_bytes(), name
    target = directory / "artifacts" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(data)

sources = ["tests/restart/recovery_offline_test.go", "tests/restart/full_state_offline_test.go"]
binaries = ["tmp/full-state-offline-windows-tests.exe", "tmp/full-state-offline-linux-tests"]
report = {
    "baseline_commit": subprocess.check_output(["git", "rev-parse", "45ad8af"], cwd=workspace, text=True).strip(),
    "toolchain": "Go 1.21.3; Windows CGO_ENABLED=0; Linux CGO_ENABLED=1 with race detection; GOMAXPROCS=2; offline cached modules; Linux network namespace isolated",
    "source_sha256": {name: digest(workspace / name) for name in sources},
    "source_git_blobs": {name: subprocess.check_output(["git", "hash-object", "--path=" + name, name], cwd=workspace, text=True).strip() for name in sources},
    "binary_sha256": {name: digest(workspace / name) for name in binaries},
    "compact_source_manifest_sha256": "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf",
    "copies_per_platform": 9,
    "files_per_initial_copy": 230,
    "bytes_per_initial_copy": 528817080,
    "cross_platform_identical_artifacts": files,
    "completed_cuts_per_platform": 9,
    "uncertain_cuts_per_platform": 2,
    "scope": "Complete preserved account state with public scalar 1/2 substitutions and retained historical header context; three controlled handover blocks. No real key, W: data, replay checkpoint, public peer or complete 117 GB database opened. No production code changed. Forced process termination, not machine power-loss testing. This is not a reproducible release-build attestation."
}
with (directory / "identities.json").open("x", encoding="utf-8", newline="\n") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
with (directory / "SHA256SUMS").open("x", encoding="utf-8", newline="\n") as output:
    for path in files:
        output.write(f"{digest(path)}  {path.relative_to(directory).as_posix()}\n")
print(f"Recorded {len(files)} evidence files; Windows/Linux blocks, plans and ledgers are byte-identical")
