import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-toolchain-resolution'
before = json.loads((root / 'tmp/fsn-stats-auth/react-frontend/package-lock.json').read_text(encoding='utf-8'))
assert before['lockfileVersion'] == 1
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
command = prefix + ['install', '--package-lock-only', '--lockfile-version=3', '--ignore-scripts', '--no-audit', '--no-fund']
with (bundle / 'modern-lock.stdout.txt').open('wb') as stdout, (bundle / 'modern-lock.stderr.txt').open('wb') as stderr:
    completed = subprocess.run(command, cwd=scratch, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
assert completed.returncode == 0
after = json.loads((scratch / 'package-lock.json').read_text(encoding='utf-8'))
assert after['lockfileVersion'] == 3


def flatten(dependencies, prefix=''):
    result = {}
    for name, value in dependencies.items():
        key = prefix + 'node_modules/' + name
        result[key] = value
        result.update(flatten(value.get('dependencies', {}), key + '/'))
    return result


old = flatten(before['dependencies'])
new = {p: v for p, v in after['packages'].items() if p}
assert old.keys() == new.keys()
for path, entry in old.items():
    for field in ['version', 'resolved', 'integrity']:
        expected = entry.get(field)
        if field == 'version' and expected.startswith('npm:'):
            alias, expected = expected[4:].rsplit('@', 1)
            assert new[path]['name'] == alias
        assert expected == new[path].get(field), (path, field)
(bundle / 'modern-lock.json').write_text(json.dumps({'command': command, 'exit': completed.returncode, 'paths': len(new), 'all_versions_archives_integrities_preserved': True, 'sha256': hashlib.sha256((scratch / 'package-lock.json').read_bytes()).hexdigest()}, indent=2) + '\n', encoding='utf-8')
print('Lock v3 preserves all', len(new), 'package versions, archives and integrity values', flush=True)
