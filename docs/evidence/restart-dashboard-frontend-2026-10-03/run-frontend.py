import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
scratch = root / 'tmp/dashboard-frontend-build'
assert not scratch.exists()
output = bundle / 'frontend-1'
output.mkdir(exist_ok=False)
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'CI=true', 'REACT_APP_STATS_API_PATH=/stats-api']
node = linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node'
records = []
for name, settings, args in [
    ('react-tests', ['REACT_APP_STATS_POLL_INTERVAL_MS=100', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS=50'], ['node_modules/react-scripts/scripts/test.js', '--watchAll=false', '--runInBand']),
    ('build', ['REACT_APP_STATS_POLL_INTERVAL_MS=250', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS=1000', 'BUILD_PATH=' + linux_root + 'tmp/dashboard-frontend-build'], ['node_modules/react-scripts/scripts/build.js']),
]:
    command = prefix + settings + [node] + args
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': name, 'command': command, 'exit': result.returncode})
    print(name, result.returncode, flush=True)
    assert result.returncode == 0
hashes = {path.relative_to(scratch).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in scratch.rglob('*') if path.is_file()}
(output / 'result.json').write_text(json.dumps({'commands': records, 'build_directory': str(scratch), 'build_sha256': hashes}, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Built', len(hashes), 'files', flush=True)
