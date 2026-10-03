import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
paths = ['README.md', 'docs/geoip-dependency-upgrade.md', 'docs/geoip-operations.md', 'docs/runtime-dependency-review.md']
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']
already_staged = subprocess.check_output(git + ['diff', '--cached', '--name-only']).decode().splitlines()
assert not already_staged or sorted(already_staged) == sorted(paths)
subprocess.run(git + ['add', '--'] + paths, check=True)
assert sorted(subprocess.check_output(git + ['diff', '--cached', '--name-only']).decode().splitlines()) == sorted(paths)
for path in paths:
    assert subprocess.check_output(git + ['show', ':' + path]) == (dashboard / path).read_bytes(), path
subprocess.run(git + ['diff', '--cached', '--check'], check=True)
(bundle / 'staged-dashboard.json').write_text(json.dumps({'paths': paths, 'exact_bytes_verified': True, 'whitespace_check': True}, indent=2) + '\n', encoding='utf-8')
print('Verified four documentation paths; application sources unchanged')
