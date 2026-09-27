import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
prefix = evidence.relative_to(workspace).as_posix()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=workspace)


identities = json.loads(git('show', ':' + prefix + '/identities.json'))
for path, expected in identities['sources'].items():
    assert git('rev-parse', ':' + path).decode().strip() == expected['git_blob'], path
checksums = git('show', ':' + prefix + '/SHA256SUMS').decode().splitlines()
for line in checksums:
    expected, name = line.split('  ', 1)
    assert hashlib.sha256(git('show', ':' + prefix + '/' + name)).hexdigest() == expected, name
authored = {'docs/restart-peer-purchase-retry.md', 'docs/restart-purchase-delivery.md', 'docs/restart-operator-recovery.md', 'docs/restart-plan.md', 'docs/restart-node-patch-review.md', 'tests/restart/README.md', 'tests/restart/full_state_delivery_linux_test.go', 'eth/restart_purchase_retry_test.go'}
expected_paths = authored | {p.relative_to(workspace).as_posix() for p in evidence.rglob('*') if p.is_file()}
actual = set(git('diff', '--cached', '--name-only').decode().splitlines())
assert actual == expected_paths, (actual - expected_paths, expected_paths - actual)
assert git('diff', '--name-only') == b''
print(f'Verified {len(identities["sources"])} source blobs, {len(checksums)} exact staged evidence checksums and {len(actual)} staged files; no unstaged tracked edits')
