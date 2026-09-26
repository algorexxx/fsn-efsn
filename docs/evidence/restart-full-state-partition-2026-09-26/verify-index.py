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
    "tests/restart/full_state_partition_linux_test.go", "tests/restart/full_state_participant_ledger_test.go", "tests/restart/README.md",
    "tests/restart/full_state_partition_diagnostic_linux_test.go", "tests/restart/node_rehearsal_linux_test.go",
    "docs/restart-full-state-partition.md", "docs/restart-full-state-participant.md", "docs/restart-operator-recovery.md", "docs/restart-plan.md",
} | {prefix + path.relative_to(evidence).as_posix() for path in evidence.rglob("*") if path.is_file()}
actual_paths = set(git("diff", "--cached", "--name-only").decode().splitlines())
assert actual_paths == expected_paths, (actual_paths - expected_paths, expected_paths - actual_paths)
print(f"Verified {len(checksums)} staged hashes, {len(identities['sources'])} source identities and exact {len(actual_paths)}-file scope")
