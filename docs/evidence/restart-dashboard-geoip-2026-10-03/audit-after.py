import hashlib
import json
import os
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'audit', '--package-lock-only', '--ignore-scripts', '--json', '--registry=https://registry.npmjs.org']
with (bundle / 'audit-after.json').open('wb') as stdout, (bundle / 'audit-after.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
audit = json.loads((bundle / 'audit-after.json').read_text(encoding='utf-8'))
assert result.returncode == 0 and 'error' not in audit
assert audit['vulnerabilities'] == {}
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
changes = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))['changes']
removed = [row['path'] for row in changes if row['after'] is None]
assert all(not (dashboard / name).exists() for name in removed)
assert not (dashboard / 'api-server/node_modules').exists()
(bundle / 'installed-packages.json').write_text(json.dumps(installed, indent=2) + '\n', encoding='utf-8', newline='\n')
record = {'command': command, 'exit': result.returncode, 'counts': audit['metadata']['vulnerabilities'], 'target_findings_absent': True, 'installed_entries_match_lock': len(installed), 'removed_paths_absent': removed}
(bundle / 'audit-after-capture.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record), flush=True)
