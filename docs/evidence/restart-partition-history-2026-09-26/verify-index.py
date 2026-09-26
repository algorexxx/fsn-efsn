import hashlib
import json
import subprocess
from pathlib import Path

evidence=Path(__file__).resolve().parent
workspace=evidence.parents[2]
prefix=evidence.relative_to(workspace).as_posix()+'/'
def git(*args):
    return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=workspace)
identities=json.loads(git('show',':'+prefix+'identities.json'))
for path,value in identities['sources'].items():
    assert git('rev-parse',':'+path).decode().strip() == value['git_blob'], path
checksums=git('show',':'+prefix+'SHA256SUMS').decode().splitlines()
for line in checksums:
    expected,path=line.split('  ',1)
    assert hashlib.sha256(git('show',':'+prefix+path)).hexdigest() == expected, path
expected_paths={
    'tests/restart/full_state_history_linux_test.go',
    'tests/restart/full_state_partition_linux_test.go',
    'tests/restart/full_state_post_sync_linux_test.go',
    'tests/restart/full_state_original_history_linux_test.go',
    'tests/restart/continuous_repair_linux_test.go',
    'tests/restart/README.md',
    'docs/restart-partition-history.md',
    'docs/restart-full-state-partition.md',
    'docs/restart-full-state-participant.md',
    'docs/restart-operator-recovery.md',
    'docs/restart-plan.md',
} | {prefix+p.relative_to(evidence).as_posix() for p in evidence.rglob('*') if p.is_file()}
actual=set(git('diff','--cached','--name-only').decode().splitlines())
assert actual == expected_paths, (actual-expected_paths,expected_paths-actual)
print(f'Verified {len(checksums)} staged hashes, {len(identities["sources"])} source identities and exact {len(actual)}-file scope')
