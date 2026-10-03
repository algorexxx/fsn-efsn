import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node', '--test', '--test-reporter=tap', 'test/history.test.cjs']
with (bundle / 'baseline-test.stdout.txt').open('wb') as stdout, (bundle / 'baseline-test.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit': result.returncode, 'lodash': json.loads((dashboard / 'node_modules/lodash/package.json').read_text(encoding='utf-8'))['version'], 'test_sha256': hashlib.sha256((dashboard / 'test/history.test.cjs').read_bytes()).hexdigest()}
(bundle / 'baseline-test.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
raise SystemExit(result.returncode)
