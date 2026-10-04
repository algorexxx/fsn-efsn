import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
baseline = json.loads((bundle / 'baseline.json').read_text(encoding='utf-8'))
command = ['git', '-C', str(dashboard)]
commit = subprocess.check_output(command + ['rev-parse', 'HEAD']).decode().strip()
assert subprocess.check_output(command + ['rev-parse', 'HEAD^']).decode().strip() == baseline['dashboard_commit']
assert subprocess.check_output(command + ['status', '--porcelain']) == b''
patch = subprocess.check_output(command + ['diff', '--binary', '--full-index', baseline['dashboard_commit'], commit])
(bundle / 'dashboard-mmdb.patch').write_bytes(patch)
value = {'base': baseline['dashboard_commit'], 'dashboard_commit': commit, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'patch_bytes': len(patch)}
(bundle / 'commit.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
print(json.dumps(value, indent=2))
