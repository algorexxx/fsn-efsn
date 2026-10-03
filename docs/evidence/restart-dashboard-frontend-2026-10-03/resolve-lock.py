import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth/react-frontend'
scratch = root / 'tmp/dashboard-frontend-resolution'
candidate = json.loads((scratch / 'package.json').read_text(encoding='utf-8'))
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
records = []
for label, operation in [('frontend', ['install'])]:
    command = prefix + operation + ['--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
    with (bundle / (label + '-resolution.stdout.txt')).open('wb') as stdout, (bundle / (label + '-resolution.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=scratch, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'command': command, 'exit': result.returncode})
    print(label, result.returncode, flush=True)
    assert result.returncode == 0
assert json.loads((scratch / 'package.json').read_text(encoding='utf-8')) == candidate
(bundle / 'resolution.json').write_text(json.dumps({'commands': records, 'cwd': str(scratch)}, indent=2) + '\n', encoding='utf-8', newline='\n')


def flatten(dependencies, prefix=''):
    result = {}
    for name, item in dependencies.items():
        key = prefix + 'node_modules/' + name
        result[key] = {field: item[field] for field in ['version', 'resolved', 'integrity'] if field in item}
        result.update(flatten(item.get('dependencies', {}), key + '/'))
    return result


old = json.loads((dashboard / 'package-lock.json').read_text(encoding='utf-8'))
new = json.loads((scratch / 'package-lock.json').read_text(encoding='utf-8'))
assert old['lockfileVersion'] == new['lockfileVersion'] == 1
assert new['dependencies']['axios']['version'] == '0.34.0'
old_entries = flatten(old['dependencies'])
new_entries = flatten(new['dependencies'])
changes = [{'path': name, 'before': old_entries.get(name), 'after': new_entries.get(name)} for name in sorted(set(old_entries) | set(new_entries)) if old_entries.get(name) != new_entries.get(name)]
summary = {'before_entries': len(old_entries), 'after_entries': len(new_entries), 'changes': changes, 'candidate_sha256': {name: hashlib.sha256((scratch / name).read_bytes()).hexdigest() for name in ['package.json', 'package-lock.json']}}
(bundle / 'lock-diff.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'before_entries': len(old_entries), 'after_entries': len(new_entries), 'changed_entries': len(changes)}))
for change in changes:
    print(change['path'], (change['before'] or {}).get('version'), '->', (change['after'] or {}).get('version'))
