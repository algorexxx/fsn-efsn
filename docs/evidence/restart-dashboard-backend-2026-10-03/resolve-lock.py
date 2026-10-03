import hashlib
import json
import os
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
scratch = root / 'tmp/dashboard-backend-resolution'
scratch.mkdir(exist_ok=True)
assert {path.name for path in scratch.iterdir()} <= {'package.json', 'package-lock.json'}
for name in ['package.json', 'package-lock.json']:
    (scratch / name).write_bytes((dashboard / name).read_bytes())
removed = ['auto-bind', 'body-parser', 'debug', 'grunt', 'grunt-contrib-clean', 'grunt-contrib-concat', 'grunt-contrib-copy', 'grunt-contrib-cssmin', 'grunt-contrib-jade', 'grunt-contrib-uglify', 'http2', 'jade']
candidate = json.loads((scratch / 'package.json').read_text(encoding='utf-8'))
for name in removed:
    del candidate['dependencies'][name]
candidate['dependencies']['lodash'] = '4.18.1'
(scratch / 'package.json').write_text(json.dumps(candidate, indent=2) + '\n', encoding='utf-8', newline='\n')
command = ['C:/Program Files/nodejs/node.exe', 'C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'install', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
environment = dict(os.environ, npm_config_cache=str(root / 'tmp/dashboard-audit-cache'))
with (bundle / 'resolve-lock.stdout.txt').open('wb') as stdout, (bundle / 'resolve-lock.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=scratch, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit': result.returncode, 'cwd': str(scratch)}
(bundle / 'resolution.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
assert result.returncode == 0
before = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
after = json.loads((scratch / 'package.json').read_text(encoding='utf-8'))
for name in removed:
    del before['dependencies'][name]
before['dependencies']['lodash'] = '4.18.1'
assert after == before


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
old_entries = flatten(old['dependencies'])
new_entries = flatten(new['dependencies'])
changes = [{'path': name, 'before': old_entries.get(name), 'after': new_entries.get(name)} for name in sorted(set(old_entries) | set(new_entries)) if old_entries.get(name) != new_entries.get(name)]
summary = {'before_entries': len(old_entries), 'after_entries': len(new_entries), 'changes': changes, 'candidate_sha256': {name: hashlib.sha256((scratch / name).read_bytes()).hexdigest() for name in ['package.json', 'package-lock.json']}}
(bundle / 'lock-diff.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'before_entries': len(old_entries), 'after_entries': len(new_entries), 'changed_entries': len(changes)}, indent=2))
for change in changes:
    print(change['path'], (change['before'] or {}).get('version'), '->', (change['after'] or {}).get('version'))
