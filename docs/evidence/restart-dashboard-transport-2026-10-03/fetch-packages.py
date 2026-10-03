import base64
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-transport-packages'
scratch.mkdir(exist_ok=True)
record = []
for name in ['primus', 'ws']:
    path = bundle.parent / 'restart-dashboard-runtime-review-2026-10-03/metadata' / (name + '-latest.json')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    url = manifest['dist']['tarball']
    assert url.startswith('https://registry.npmjs.org/' + name + '/-/')
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(4 * 1024 * 1024)
        assert not response.read(1)
    algorithm, encoded = manifest['dist']['integrity'].split('-', 1)
    assert algorithm == 'sha512'
    assert base64.b64encode(hashlib.sha512(data).digest()).decode() == encoded
    archive = scratch / (name + '-' + manifest['version'] + '.tgz')
    archive.write_bytes(data)
    directory = scratch / name
    directory.mkdir(exist_ok=True)
    selected = ['package.json', 'transformers/websockets/server.js', 'transformers/websockets/client.js', 'spark.js', 'index.js', 'README.md', 'SECURITY.md'] if name == 'primus' else ['package.json', 'lib/websocket-server.js', 'lib/receiver.js', 'README.md']
    files = {}
    with tarfile.open(archive, 'r:gz') as tar:
        members = {member.name: member for member in tar.getmembers()}
        for relative in selected:
            member = members.get('package/' + relative)
            if member is None:
                continue
            assert member.isfile() and member.size < 2 * 1024 * 1024
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            content = tar.extractfile(member).read()
            target.write_bytes(content)
            files[relative] = hashlib.sha256(content).hexdigest()
    record.append({'name': name, 'version': manifest['version'], 'url': url, 'integrity': manifest['dist']['integrity'], 'archive_sha256': hashlib.sha256(data).hexdigest(), 'selected_files_sha256': files})
(bundle / 'package-inspection.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps([{'name': row['name'], 'version': row['version']} for row in record]))
