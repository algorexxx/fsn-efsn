import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
node = Path('C:/Program Files/nodejs/node.exe')
npm = Path('C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js')
record = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'commands': [], 'inputs': {}}
paths = ['package.json', 'package-lock.json', 'react-frontend/package.json', 'react-frontend/package-lock.json', 'api-server/package.json', 'api-server/package-lock.json']
for name in paths:
    raw = (dashboard / name).read_bytes()
    record['inputs'][name] = hashlib.sha256(raw).hexdigest()
    destination = bundle / 'inputs' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
record['dashboard_commit'] = subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip()
record['node_version'] = subprocess.check_output([str(node), '--version']).decode().strip()
record['npm_version'] = subprocess.check_output([str(node), str(npm), '--version']).decode().strip()
environment = dict(os.environ, npm_config_cache=str(root / 'tmp/dashboard-audit-cache'))
for label, directory in [('backend', dashboard), ('frontend', dashboard / 'react-frontend'), ('legacy-api', dashboard / 'api-server')]:
    args = [str(node), str(npm), 'audit', '--package-lock-only', '--ignore-scripts', '--json', '--registry=https://registry.npmjs.org']
    with (bundle / (label + '-audit.json')).open('wb') as stdout, (bundle / (label + '-audit.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(args, cwd=directory, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    value = json.loads((bundle / (label + '-audit.json')).read_text(encoding='utf-8'))
    item = {'name': label, 'args': args[2:], 'exit': result.returncode, 'metadata': value.get('metadata'), 'error': value.get('error')}
    record['commands'].append(item)
    print(json.dumps(item), flush=True)
record['inputs_unchanged'] = all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == value for name, value in record['inputs'].items())
assert record['inputs_unchanged']
(bundle / 'audit-capture.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
assert all(item['exit'] in [0, 1] and item['metadata'] is not None and item['error'] is None for item in record['commands'])
