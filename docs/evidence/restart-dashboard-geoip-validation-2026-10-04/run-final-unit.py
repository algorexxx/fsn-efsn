import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', runtime, '--test', '--test-reporter=tap', 'test/geoip-dataset.test.cjs']
with (bundle / 'unit.stdout.txt').open('wb') as stdout, (bundle / 'unit.stderr.txt').open('wb') as stderr:
    completed = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'exit': completed.returncode, 'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in ['lib/geoip-dataset.js', 'deploy/validate-geoip.cjs', 'test/geoip-dataset.test.cjs', 'test/fixtures/geoip-data.json']}}
(bundle / 'unit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
assert completed.returncode == 0
print(json.dumps(record))
