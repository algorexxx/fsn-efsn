import hashlib
import json
import subprocess
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
scratch = root / 'tmp/dashboard-runtime-review/node24-build'
output = bundle / 'node24-build'
output.mkdir(exist_ok=False)
assert not scratch.exists()
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
environment = {
    'CI': 'true',
    'REACT_APP_STATS_API_PATH': '/stats-api',
    'REACT_APP_STATS_POLL_INTERVAL_MS': '250',
    'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '1000',
    'BUILD_PATH': '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/node24-build',
}
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env']
command += [name + '=' + value for name, value in environment.items()]
command += [runtime, 'node_modules/react-scripts/scripts/build.js']
started = time.monotonic()
with (output / 'stdout.txt').open('wb') as stdout, (output / 'stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard / 'react-frontend', stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
files = {path.relative_to(scratch).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in scratch.rglob('*') if path.is_file()}
record = {'command': command, 'exit': result.returncode, 'elapsed_seconds': round(time.monotonic() - started, 3), 'output': str(scratch), 'file_sha256': files}
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({key: value for key, value in record.items() if key != 'file_sha256'}), flush=True)
print('files', len(files), flush=True)
raise SystemExit(result.returncode)
