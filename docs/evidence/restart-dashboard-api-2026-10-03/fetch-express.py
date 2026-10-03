import base64
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-api-packages'
scratch.mkdir(exist_ok=True)
url = 'https://registry.npmjs.org/express'
with urllib.request.urlopen(url, timeout=30) as response:
    registry = response.read(8 * 1024 * 1024)
    assert not response.read(1)
metadata = json.loads(registry)
versions = sorted((value for value in metadata['versions'] if value.startswith('4.') and all(part.isdecimal() for part in value.split('.'))), key=lambda value: tuple(map(int, value.split('.'))))
version = versions[-1]
manifest = metadata['versions'][version]
(bundle / 'express-selected.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
selection = {'registry': url, 'registry_sha256': hashlib.sha256(registry).hexdigest(), 'stable_4x_versions': versions, 'selected': version, 'published': metadata['time'][version], 'dist_tags': metadata['dist-tags']}
(bundle / 'version-selection.json').write_text(json.dumps(selection, indent=2) + '\n', encoding='utf-8', newline='\n')
url = manifest['dist']['tarball']
assert url == 'https://registry.npmjs.org/express/-/express-' + version + '.tgz'
with urllib.request.urlopen(url, timeout=30) as response:
    data = response.read(4 * 1024 * 1024)
    assert not response.read(1)
algorithm, encoded = manifest['dist']['integrity'].split('-', 1)
assert algorithm == 'sha512' and base64.b64encode(hashlib.sha512(data).digest()).decode() == encoded
archive = scratch / ('express-' + version + '.tgz')
archive.write_bytes(data)
files = {}
with tarfile.open(archive, 'r:gz') as tar:
    for name in ['package.json', 'History.md', 'lib/application.js', 'lib/middleware/query.js', 'lib/router/index.js', 'LICENSE']:
        member = tar.getmember('package/' + name)
        assert member.isfile() and member.size < 2 * 1024 * 1024
        content = tar.extractfile(member).read()
        target = scratch / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        files[name] = hashlib.sha256(content).hexdigest()
record = {'name': 'express', 'version': version, 'url': url, 'integrity': manifest['dist']['integrity'], 'archive_sha256': hashlib.sha256(data).hexdigest(), 'selected_files_sha256': files}
(bundle / 'package-inspection.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'version': version, 'published': selection['published'], 'dependencies': manifest['dependencies'], 'sri_verified': True}, indent=2))
