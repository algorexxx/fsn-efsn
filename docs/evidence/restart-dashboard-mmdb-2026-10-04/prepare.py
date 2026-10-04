import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
paths = subprocess.check_output(['git', '-C', str(dashboard), 'ls-files', '-z']).decode().split('\0')
baseline = {'dashboard_commit': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip(), 'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in paths if name}}
assert baseline['dashboard_commit'] == '2e047abb1eaab6e9315373e39af68212a399b451'
assert subprocess.check_output(['git', '-C', str(dashboard), 'status', '--porcelain']) == b''
(bundle / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8')
manifest = json.loads((bundle.parent / 'restart-dashboard-geoip-reader-2026-10-04/fixtures.json').read_text(encoding='utf-8'))
fixtures = dashboard / 'test/fixtures/geoip'
fixtures.mkdir(exist_ok=False)
for source, name in [('test-data/GeoLite2-City-Test.mmdb', 'city.mmdb'), ('test-data/MaxMind-DB-test-ipv6-24.mmdb', 'not-city.mmdb'), ('LICENSE-MIT', 'LICENSE-MIT')]:
    data = (root / 'tmp/dashboard-geoip-reader/upstream' / source).read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest[source]['sha256']
    (fixtures / name).write_bytes(data)
print('Captured source baseline and copied verified small synthetic fixtures.')
