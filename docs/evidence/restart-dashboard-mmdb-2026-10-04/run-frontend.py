import hashlib
import json
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
scratch = frontend / 'build' if sys.argv[1] == '2' else root / 'tmp/dashboard-mmdb-build'
output = bundle / ('frontend-' + sys.argv[1])
output.mkdir(exist_ok=False)
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
runtime = linux_root + 'tmp/dashboard-runtime-review/v24.21.0'
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
path = subprocess.check_output(wsl + ['printenv', 'PATH']).decode().strip()
shim = root / 'tmp/dashboard-toolchain-bin'
shim.mkdir(exist_ok=True)
(shim / 'npm').write_text('#!/bin/sh\nexec "' + runtime + '/node" "/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js" "$@"\n', encoding='utf-8', newline='\n')
subprocess.run(wsl + ['chmod', '+x', linux_root + 'tmp/dashboard-toolchain-bin/npm'], check=True)
prefix = wsl + ['env', 'PATH=' + linux_root + 'tmp/dashboard-toolchain-bin:' + runtime + ':' + path, 'CI=true', 'REACT_APP_STATS_API_PATH=/stats-api']
npm = [runtime + '/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
records = []
for name, settings, args in [
    ('react-tests', ['REACT_APP_STATS_POLL_INTERVAL_MS=100', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS=50'], ['test', '--', '--watchAll=false', '--runInBand']),
    ('build', ['REACT_APP_STATS_POLL_INTERVAL_MS=250', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS=1000'] + ([] if sys.argv[1] == '2' else ['BUILD_PATH=' + linux_root + 'tmp/dashboard-mmdb-build']), ['run', 'build']),
]:
    if name == 'react-tests' and sys.argv[1] == '2':
        continue
    command = prefix + settings + npm + args
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': name, 'command': command, 'exit': result.returncode})
    print(name, result.returncode, flush=True)
hashes = {p.relative_to(scratch).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in scratch.rglob('*') if p.is_file()} if all(r['exit'] == 0 for r in records) else {}
(output / 'result.json').write_text(json.dumps({'commands': records, 'build_directory': str(scratch), 'build_sha256': hashes}, indent=2) + '\n', encoding='utf-8')
assert all(r['exit'] == 0 for r in records)
print('Built', len(hashes), 'files', flush=True)
