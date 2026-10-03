import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
repository = bundle.parents[2]
dashboard = repository / 'tmp/fsn-stats-auth'
attempt = bundle / sys.argv[1]
attempt.mkdir(exist_ok=False)
node = 'C:/Program Files/nodejs/node.exe'
files = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=dashboard).decode('utf-8').splitlines()
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(set(files))}
(attempt / 'source-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
environment = {**os.environ, 'CI': 'true', 'REACT_APP_STATS_API_PATH': '/stats-api', 'REACT_APP_STATS_POLL_INTERVAL_MS': '100', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '50'}
environment.pop('NODE_OPTIONS', None)
commands = [(name.replace(':', '-'), [node, *package['scripts'][name].split()[1:]], dashboard) for name in ['test', 'test:wire']]
commands += [('react-tests', [node, 'node_modules/react-scripts/scripts/test.js', '--watchAll=false', '--runInBand'], dashboard / 'react-frontend'), ('build', [node, 'node_modules/react-scripts/scripts/build.js'], dashboard / 'react-frontend')]
if len(sys.argv) > 2 and sys.argv[2] == 'frontend':
    commands = commands[-2:]
results = []
for label, command, cwd in commands:
    if label == 'build':
        environment.update(REACT_APP_STATS_POLL_INTERVAL_MS='250', REACT_APP_STATS_REQUEST_TIMEOUT_MS='1000')
    started = time.time()
    with (attempt / f'{label}.stdout.txt').open('wb') as output, (attempt / f'{label}.stderr.txt').open('wb') as error:
        result = subprocess.run(command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL, stdout=output, stderr=error, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': label, 'command': command, 'exit_code': result.returncode, 'seconds': time.time() - started})
    print(json.dumps(results[-1]), flush=True)
(attempt / 'results.json').write_text(json.dumps({'node': subprocess.check_output([node, '--version']).decode().strip(), 'results': results}, indent=2) + '\n', encoding='utf-8')
if results[-1]['exit_code'] == 0:
    build = dashboard / 'react-frontend/build'
    build_hashes = {str(path.relative_to(build)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(build.rglob('*')) if path.is_file()}
    (attempt / 'build-sha256.json').write_text(json.dumps(build_hashes, indent=2) + '\n', encoding='utf-8')
sys.exit(int(any(result['exit_code'] != 0 for result in results)))
