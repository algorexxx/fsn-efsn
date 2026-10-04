import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
paths = ['README.md', 'deploy/validate-geoip.cjs', 'docs/deployment-configuration.md', 'docs/geoip-operations.md', 'docs/geoip-validation.md', 'docs/geoip-mmdb.md', 'lib/deployment-config.js', 'lib/geoip-dataset.js', 'lib/geoip.js', 'lib/node.js', 'package.json', 'package-lock.json', 'react-frontend/src/App.test.js', 'react-frontend/src/snapshot-view.js', 'server.js', 'test/browser-snapshot.test.cjs', 'test/collector-input.test.cjs', 'test/efsn-telemetry.test.cjs', 'test/fixtures/browser-server.cjs', 'test/fixtures/collector-environment.cjs', 'test/fixtures/collector.cjs', 'test/fixtures/efsn-wsl-server.cjs', 'test/fixtures/geoip-data.json', 'test/geoip-dataset.test.cjs', 'test/geoip.test.cjs']
paths += ['test/fixtures/geoip/' + name for name in ['city.mmdb', 'not-city.mmdb', 'LICENSE-MIT', 'README.md']]
retired = {'lib/geoip-dataset.js', 'test/geoip-dataset.test.cjs', 'test/fixtures/geoip-data.json'}
command = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false']
assert subprocess.check_output(command + ['diff', '--cached', '--name-only']) == b''
subprocess.run(command + ['add', '--'] + paths, check=True)
staged = subprocess.check_output(command + ['diff', '--cached', '--name-only', '-z']).decode().split('\0')
assert sorted(name for name in staged if name) == sorted(paths)
normalized = []
for name in paths:
    path = dashboard / name
    if name in retired:
        assert not path.exists()
        continue
    actual = subprocess.check_output(command + ['show', ':' + name])
    expected = path.read_bytes()
    if actual != expected:
        assert path.suffix in ['.md', '.js', '.cjs', '.json'] and actual == expected.replace(b'\r\n', b'\n'), name
        normalized.append(name)
subprocess.run(command + ['-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--cached', '--check'], check=True)
(bundle / 'staged-dashboard.json').write_text(json.dumps({'files': sorted(paths), 'line_endings_normalized_by_git': normalized}, indent=2) + '\n', encoding='utf-8')
print('Verified', len(paths), 'staged dashboard files and removals.')
