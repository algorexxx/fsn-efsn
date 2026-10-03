import base64
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-geoip-packages'
scratch.mkdir(exist_ok=True)
records = []
for name, major, limit in [('geoip-lite', 2, 64 * 1024 * 1024), ('color-string', 1, 1024 * 1024)]:
    url = 'https://registry.npmjs.org/' + name
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read(8 * 1024 * 1024)
        assert not response.read(1)
    registry = json.loads(raw)
    versions = sorted((value for value in registry['versions'] if value.startswith(str(major) + '.') and all(part.isdecimal() for part in value.split('.'))), key=lambda value: tuple(map(int, value.split('.'))))
    version = versions[-1]
    manifest = registry['versions'][version]
    (bundle / (name + '-selected.json')).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    archive_url = manifest['dist']['tarball']
    assert archive_url == 'https://registry.npmjs.org/' + name + '/-/' + name + '-' + version + '.tgz'
    archive = scratch / (name + '-' + version + '.tgz')
    with urllib.request.urlopen(archive_url, timeout=30) as response:
        data = response.read(limit)
        assert not response.read(1)
    algorithm, encoded = manifest['dist']['integrity'].split('-', 1)
    assert algorithm == 'sha512' and base64.b64encode(hashlib.sha512(data).digest()).decode() == encoded
    archive.write_bytes(data)
    directory = scratch / name
    directory.mkdir(exist_ok=True)
    files = {}
    members = []
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            members.append({'name': member.name, 'bytes': member.size, 'mtime': member.mtime})
            relative = Path(member.name).relative_to('package')
            if not member.isfile() or member.size > 2 * 1024 * 1024:
                continue
            if relative.parts[0] == 'data':
                continue
            target = (directory / relative).resolve()
            assert target.is_relative_to(directory.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            content = tar.extractfile(member).read()
            target.write_bytes(content)
            files[relative.as_posix()] = hashlib.sha256(content).hexdigest()
    record = {'name': name, 'version': version, 'published': registry['time'][version], 'registry': url, 'registry_sha256': hashlib.sha256(raw).hexdigest(), 'stable_major_versions': versions, 'url': archive_url, 'integrity': manifest['dist']['integrity'], 'archive_sha256': hashlib.sha256(data).hexdigest(), 'archive_bytes': len(data), 'selected_files_sha256': files, 'members': members}
    records.append(record)
    print(json.dumps({'name': name, 'version': version, 'published': record['published'], 'engines': manifest.get('engines'), 'archive_bytes': len(data), 'unpacked_bytes': manifest['dist'].get('unpackedSize'), 'dependencies': manifest.get('dependencies'), 'scripts': manifest.get('scripts')}), flush=True)
(bundle / 'package-inspection.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8', newline='\n')
