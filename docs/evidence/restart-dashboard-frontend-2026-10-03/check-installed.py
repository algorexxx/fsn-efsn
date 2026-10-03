import hashlib
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
lock = json.loads((frontend / 'package-lock.json').read_text(encoding='utf-8'))
installed = []
omitted = []


def inspect(dependencies, prefix='node_modules/'):
    for name, value in dependencies.items():
        path = prefix + name
        manifest = frontend / path / 'package.json'
        if not manifest.exists():
            assert value.get('optional'), path
            omitted.append({'path': path, 'version': value['version'], 'optional': True})
            continue
        data = manifest.read_bytes()
        assert json.loads(data)['version'] == value['version'], path
        installed.append({'path': path, 'version': value['version'], 'package_sha256': hashlib.sha256(data).hexdigest()})
        inspect(value.get('dependencies', {}), path + '/node_modules/')


inspect(lock['dependencies'])
inspection = json.loads((bundle / 'package-inspection.json').read_text(encoding='utf-8'))
for name, value in inspection['files'].items():
    path = frontend / 'node_modules/axios' / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == value['sha256'], name
changes = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))['changes']
removed = [row['path'] for row in changes if row['after'] is None]
assert all(not (frontend / path).exists() for path in removed)
record = {'installed': installed, 'omitted_optional': omitted, 'removed_paths_absent': removed, 'all_axios_archive_files_match': True}
(bundle / 'installed-packages.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'installed': len(installed), 'omitted': omitted, 'removed_paths_absent': len(removed), 'axios_archive_files': len(inspection['files'])}))
