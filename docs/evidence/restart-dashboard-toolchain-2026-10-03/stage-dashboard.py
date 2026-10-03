import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
manifest = dashboard / 'react-frontend/package.json'
manifest.write_bytes(manifest.read_bytes().replace(b'\r\n', b'\n'))
paths = [
    'README.md', 'docs/build-validation.md', 'docs/frontend-dependency-upgrade.md', 'docs/runtime-dependency-review.md', 'docs/toolchain-upgrade.md',
    'react-frontend/README.md', 'react-frontend/package.json', 'react-frontend/package-lock.json', 'react-frontend/public/index.html',
    'react-frontend/src/Components/timeAgo/customStrings.js', 'react-frontend/.oxlintrc.json', 'react-frontend/LINT-LICENSE.txt',
    'react-frontend/eslint.config.cjs', 'react-frontend/jest.config.cjs', 'react-frontend/rsbuild.config.mjs',
    'react-frontend/test/file-mock.cjs', 'react-frontend/test/style-mock.cjs',
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
