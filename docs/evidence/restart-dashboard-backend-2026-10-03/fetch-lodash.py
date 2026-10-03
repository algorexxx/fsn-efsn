import base64
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-backend-packages'
scratch.mkdir(exist_ok=True)
metadata_url = 'https://registry.npmjs.org/lodash/4.18.1'
with urllib.request.urlopen(metadata_url, timeout=30) as response:
    metadata = response.read(1024 * 1024)
manifest = json.loads(metadata)
assert manifest['name'] == 'lodash' and manifest['version'] == '4.18.1'
(bundle / 'lodash-4.18.1.json').write_bytes(metadata)
url = manifest['dist']['tarball']
assert url == 'https://registry.npmjs.org/lodash/-/lodash-4.18.1.tgz'
with urllib.request.urlopen(url, timeout=30) as response:
    data = response.read(4 * 1024 * 1024)
    assert not response.read(1)
algorithm, encoded = manifest['dist']['integrity'].split('-', 1)
assert algorithm == 'sha512'
assert base64.b64encode(hashlib.sha512(data).digest()).decode() == encoded
archive = scratch / 'lodash-4.18.1.tgz'
archive.write_bytes(data)
files = {}
with tarfile.open(archive, 'r:gz') as tar:
    for name in ['package.json', 'lodash.js', 'find.js', 'maxBy.js', 'minBy.js', 'orderBy.js', 'LICENSE']:
        member = tar.getmember('package/' + name)
        assert member.isfile() and member.size < 2 * 1024 * 1024
        content = tar.extractfile(member).read()
        (scratch / name).write_bytes(content)
        files[name] = hashlib.sha256(content).hexdigest()
record = {'metadata_url': metadata_url, 'url': url, 'integrity': manifest['dist']['integrity'], 'archive_sha256': hashlib.sha256(data).hexdigest(), 'selected_files_sha256': files}
(bundle / 'package-inspection.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'name': manifest['name'], 'version': manifest['version'], 'sri_verified': True, 'install_script': manifest.get('scripts', {}).get('install')}))
