import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
baseline = json.loads((bundle / 'baseline.json').read_text(encoding='utf-8'))
candidate = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
for label, directory in [('before', frontend), ('after', root / 'tmp/dashboard-frontend-resolution')]:
    command = prefix + ['audit', '--package-lock-only', '--ignore-scripts', '--json', '--registry=https://registry.npmjs.org']
    with (bundle / ('audit-' + label + '.json')).open('wb') as stdout, (bundle / ('audit-' + label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    audit = json.loads((bundle / ('audit-' + label + '.json')).read_text(encoding='utf-8'))
    assert result.returncode in [0, 1] and 'error' not in audit
    print(label, audit['metadata']['vulnerabilities'], flush=True)
for name in ['package.json', 'package-lock.json']:
    assert hashlib.sha256((frontend / name).read_bytes()).hexdigest() == baseline['source_sha256']['react-frontend/' + name]
    data = (root / 'tmp/dashboard-frontend-resolution' / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == candidate['candidate_sha256'][name]
    (frontend / name).write_bytes(data)
command = prefix + ['ci', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
with (bundle / 'install.stdout.txt').open('wb') as stdout, (bundle / 'install.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit': result.returncode, 'cwd': str(frontend), 'locked_inputs_unchanged': all(hashlib.sha256((frontend / name).read_bytes()).hexdigest() == value for name, value in candidate['candidate_sha256'].items())}
(bundle / 'installation.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record), flush=True)
assert result.returncode == 0 and record['locked_inputs_unchanged']
