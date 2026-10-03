import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
paths = ['README.md', 'docs/geoip-operations.md', 'docs/geoip-validation.md', 'docs/runtime-dependency-review.md', 'package.json', 'deploy/validate-geoip.cjs', 'lib/geoip-dataset.js', 'test/collector-output-wire.test.cjs', 'test/fixtures/geoip-data.json', 'test/geoip-dataset.test.cjs']
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']
assert not subprocess.check_output(git + ['diff', '--cached', '--name-only']).strip()
subprocess.run(git + ['add', '--'] + paths, check=True)
assert sorted(subprocess.check_output(git + ['diff', '--cached', '--name-only']).decode().splitlines()) == sorted(paths)
for path in paths:
    assert subprocess.check_output(git + ['show', ':' + path]) == (dashboard / path).read_bytes(), path
subprocess.run(git + ['diff', '--cached', '--check'], check=True)
(bundle / 'staged-dashboard.json').write_text(json.dumps({'paths': paths, 'exact_bytes_verified': True, 'whitespace_check': True}, indent=2) + '\n', encoding='utf-8')
print('Verified ten staged dashboard paths')
