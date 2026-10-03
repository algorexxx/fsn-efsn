import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
baseline = json.loads((bundle / 'baseline.json').read_text(encoding='utf-8'))
candidate = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))
for name in ['package.json', 'package-lock.json']:
    assert hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == baseline['source_sha256'][name]
    data = (root / 'tmp/dashboard-geoip-resolution' / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == candidate['candidate_sha256'][name]
    (dashboard / name).write_bytes(data)
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'ci', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']
with (bundle / 'install.stdout.txt').open('wb') as stdout, (bundle / 'install.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit': result.returncode, 'cwd': str(dashboard), 'locked_inputs_unchanged': all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == value for name, value in candidate['candidate_sha256'].items())}
(bundle / 'installation.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record), flush=True)
assert result.returncode == 0 and record['locked_inputs_unchanged']
