import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
paths = [
    'README.md', 'docs/browser-freshness.md', 'docs/deployment-configuration.md', 'docs/ui-maintenance.md',
    'react-frontend/README.md', 'react-frontend/src/Components/Main.js',
    'react-frontend/src/pinned-nodes.js', 'react-frontend/src/pinned-nodes.test.js',
]
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']
already_staged = subprocess.check_output(git + ['diff', '--cached', '--name-only']).decode().splitlines()
assert not already_staged or sorted(already_staged) == sorted(paths)
subprocess.run(git + ['add', '--'] + paths, check=True)
actual = subprocess.check_output(git + ['diff', '--cached', '--name-only']).decode().splitlines()
assert sorted(actual) == sorted(paths)
for path in paths:
    staged = subprocess.check_output(git + ['show', ':' + path])
    assert staged == (dashboard / path).read_bytes(), path
checked = subprocess.run(git + ['diff', '--cached', '--check'], capture_output=True)
(bundle / 'staged-dashboard-check.txt').write_bytes(checked.stdout + checked.stderr)
assert checked.returncode == 0
(bundle / 'staged-dashboard.json').write_text(json.dumps({'paths': paths, 'exact_bytes_verified': True, 'whitespace_check': 'Standard checks with CRLF line endings recognized'}, indent=2) + '\n', encoding='utf-8')
print('Verified', len(paths), 'staged dashboard paths')
