import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
git = ['git', '-C', str(root / 'tmp/fsn-stats-auth'), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
assert base == '10c780ddeb15ffdeec4d671b58d9c85d7db2ca5b'
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-profile.patch').write_bytes(patch)
artifacts = {'node': Path('C:/Program Files/nodejs/node.exe'), 'postgres': Path('C:/Program Files/PostgreSQL/18/bin/postgres.exe')}
record = {'dashboard_commit': commit, 'base': base, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'runtime': {name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in artifacts.items()}}
(bundle / 'commit.json').write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'dashboard_commit': commit, 'base': base}))
