import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
assert base == json.loads((bundle / 'source-baseline.json').read_text(encoding='utf-8'))['dashboard_commit']
assert not subprocess.check_output(git + ['status', '--porcelain']).strip()
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-geoip-validation.patch').write_bytes(patch)
paths = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
assert sorted(paths) == sorted(json.loads((bundle / 'staged-dashboard.json').read_text(encoding='utf-8'))['paths'])
record = {'dashboard_commit': commit, 'base': base, 'branch': subprocess.check_output(git + ['branch', '--show-current']).decode().strip(), 'patch_sha256': hashlib.sha256(patch).hexdigest()}
(bundle / 'commit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
