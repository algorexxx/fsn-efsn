import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
if base != '6893caa09e0db17d8b0f70a5d8349c1fb5bbb2c2':
    raise ValueError('Unexpected dashboard base')
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-output.patch').write_bytes(patch)
record = {'dashboard_commit': commit, 'base': base, 'branch': subprocess.check_output(git + ['branch', '--show-current']).decode().strip(), 'patch_sha256': hashlib.sha256(patch).hexdigest()}
(bundle / 'commit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
