import hashlib
import json
import os
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
node = 'C:/Program Files/nodejs/node.exe'
npm = 'C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js'
environment = dict(os.environ, npm_config_cache=str(root / 'tmp/dashboard-audit-cache'))
command = [node, npm, 'audit', '--package-lock-only', '--ignore-scripts', '--json', '--registry=https://registry.npmjs.org']
with (bundle / 'audit-after.json').open('wb') as stdout, (bundle / 'audit-after.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
audit = json.loads((bundle / 'audit-after.json').read_text(encoding='utf-8'))
assert result.returncode == 1 and 'error' not in audit
assert all(name not in audit['vulnerabilities'] for name in ['ws', 'primus', 'setheader', 'express', 'body-parser', 'cookie', 'debug', 'ms', 'path-to-regexp', 'qs', 'send', 'serve-static'])
lock = json.loads((dashboard / 'package-lock.json').read_text(encoding='utf-8'))
installed = []


def inspect(dependencies, prefix='node_modules/'):
    for name, value in dependencies.items():
        path = prefix + name
        manifest = json.loads((dashboard / path / 'package.json').read_text(encoding='utf-8'))
        assert manifest['version'] == value['version'], path
        installed.append({'path': path, 'version': manifest['version'], 'package_sha256': hashlib.sha256((dashboard / path / 'package.json').read_bytes()).hexdigest()})
        inspect(value.get('dependencies', {}), path + '/node_modules/')


inspect(lock['dependencies'])
(bundle / 'installed-packages.json').write_text(json.dumps(installed, indent=2) + '\n', encoding='utf-8', newline='\n')
record = {'command': command, 'exit': result.returncode, 'counts': audit['metadata']['vulnerabilities'], 'target_findings_absent': True, 'installed_entries_match_lock': len(installed)}
(bundle / 'audit-after-capture.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record), flush=True)
