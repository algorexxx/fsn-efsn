import hashlib
import json
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-geoip-reader'
acquisition = json.loads((bundle / 'acquisition.json').read_text(encoding='utf-8'))
commit = acquisition['fixture_commit']
tree = json.loads((bundle / 'fixture-tree.json').read_text(encoding='utf-8'))
entries = {row['path']: row for row in tree['tree']}
paths = ['LICENSE-MIT', 'test-data/README.md', 'cmd/write-test-data/main.go', 'source-data/GeoLite2-City-Test.json', 'test-data/GeoLite2-City-Test.mmdb', 'test-data/MaxMind-DB-test-ipv6-24.mmdb', 'test-data/MaxMind-DB-test-ipv6-28.mmdb', 'test-data/MaxMind-DB-test-ipv6-32.mmdb']
paths += ['pkg/writer/ip.go', 'pkg/writer/maxmind.go']
manifest = {}
for name in paths:
    entry = entries[name]
    if entry['size'] > 500000:
        raise ValueError('Fixture exceeds review budget')
    url = 'https://raw.githubusercontent.com/maxmind/MaxMind-DB/' + commit + '/' + name
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(500001)
    git_digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if git_digest != entry['sha'] or len(data) != entry['size']:
        raise ValueError('Fixture bytes differ from pinned tree: ' + name)
    target = scratch / 'upstream' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    manifest[name] = {'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'git_blob': git_digest}
(bundle / 'fixtures.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files': len(manifest), 'bytes': sum(value['bytes'] for value in manifest.values()), 'source_paths': [name for name in entries if name.endswith('.go')]}, indent=2))
