import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
assert not subprocess.check_output(git + ['status', '--porcelain']).strip()
names = subprocess.check_output(git + ['ls-files']).decode().splitlines()
efsn = subprocess.check_output(['git', '-C', str(root), 'ls-files', '*.go', 'go.mod', 'go.sum']).decode().splitlines()
record = {
    'dashboard_commit': subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip(),
    'dashboard_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names},
    'efsn_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in efsn},
}
(bundle / 'source-baseline.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'dashboard_files': len(names), 'efsn_files': len(efsn)}))
