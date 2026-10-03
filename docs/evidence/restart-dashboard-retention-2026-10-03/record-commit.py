import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
assert base == 'e69fe7982049dad5621871d6d96f380624e148af'
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-retention.patch').write_bytes(patch)
previous = json.loads((bundle.parent / 'restart-dashboard-presentation-2026-10-03/commit.json').read_text(encoding='utf-8'))
for artifact in previous['artifacts'].values():
    assert hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest() == artifact['sha256']
record = {'dashboard_commit': commit, 'base': base, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'artifacts': previous['artifacts'], 'reused_from': 'restart-dashboard-presentation-2026-10-03/commit.json'}
(bundle / 'commit.json').write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'dashboard_commit': commit, 'base': base}))
