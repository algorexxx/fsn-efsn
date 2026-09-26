import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
prefix = evidence.relative_to(workspace).as_posix() + "/"


def git(*args):
    return subprocess.check_output(["git", "-c", "core.safecrlf=false", *args], cwd=workspace)


identities = json.loads(git("show", ":" + prefix + "identities.json"))
for name, identity in identities["sources"].items():
    assert git("rev-parse", ":" + name).decode().strip() == identity["git_blob"], name
checksums = git("show", ":" + prefix + "SHA256SUMS").decode().splitlines()
for line in checksums:
    expected, name = line.split("  ", 1)
    assert hashlib.sha256(git("show", ":" + prefix + name)).hexdigest() == expected, name
expected_paths = {
    "tests/restart/node_rehearsal_linux_test.go",
    "tests/restart/dense_miner_fixture_linux_test.go",
    "tests/restart/continuous_partition_linux_test.go",
    "tests/restart/README.md",
    "docs/restart-continuous-partitions.md",
    "docs/restart-miner-partitions.md",
    "docs/restart-purchase-nonce-rollback.md",
    "docs/restart-plan.md",
} | {prefix + path.name for path in evidence.iterdir() if path.is_file()}
actual_paths = set(git("diff", "--cached", "--name-only").decode().splitlines())
assert actual_paths == expected_paths, (actual_paths - expected_paths, expected_paths - actual_paths)
print(f"Verified {len(checksums)} staged checksums, {len(identities['sources'])} source identities and exact {len(actual_paths)}-file scope")
