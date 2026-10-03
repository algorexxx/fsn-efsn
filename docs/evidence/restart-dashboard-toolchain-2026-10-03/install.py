import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
scratch = root / 'tmp/dashboard-toolchain-resolution'


def flatten(dependencies, prefix=''):
    result = {}
    for name, item in dependencies.items():
        key = prefix + 'node_modules/' + name
        result[key] = {field: item[field] for field in ['version', 'resolved', 'integrity'] if field in item}
        result.update(flatten(item.get('dependencies', {}), key + '/'))
    return result


old = json.loads((bundle / 'inputs/package-lock.json').read_text(encoding='utf-8'))
new = json.loads((scratch / 'package-lock.json').read_text(encoding='utf-8'))
manifest = json.loads((scratch / 'package.json').read_text(encoding='utf-8'))
assert old['lockfileVersion'] == new['lockfileVersion'] == 1
for name in manifest['dependencies']:
    assert old['dependencies'][name]['version'] == new['dependencies'][name]['version'], name
before, after = flatten(old['dependencies']), flatten(new['dependencies'])
changes = [{'path': p, 'before': before.get(p), 'after': after.get(p)} for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
assert not any(p.endswith('/react-scripts') or p.endswith('/eslint') for p in after)
audit = json.loads((bundle / 'audit-final.stdout.txt').read_text(encoding='utf-8'))
assert audit['metadata']['vulnerabilities']['total'] == 0
(bundle / 'lock-diff.json').write_text(json.dumps({'before': len(before), 'after': len(after), 'changes': changes, 'active_direct_versions_preserved': True}, indent=2) + '\n', encoding='utf-8')
print('Lock paths', len(before), '->', len(after), 'changed paths', len(changes), flush=True)
for name in ['package.json', 'package-lock.json']:
    (frontend / name).write_bytes((scratch / name).read_bytes())
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'ci', '--ignore-scripts', '--no-audit', '--no-fund']
with (bundle / 'install.stdout.txt').open('wb') as stdout, (bundle / 'install.stderr.txt').open('wb') as stderr:
    completed = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit': completed.returncode, 'sha256': {name: hashlib.sha256((frontend / name).read_bytes()).hexdigest() for name in ['package.json', 'package-lock.json']}}
(bundle / 'install.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('Install exit', completed.returncode)
assert completed.returncode == 0
