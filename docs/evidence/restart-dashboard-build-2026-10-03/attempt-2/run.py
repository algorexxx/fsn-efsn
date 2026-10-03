import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
dashboard = workspace / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
output = evidence / sys.argv[1]
output.mkdir(exist_ok=False)
node = 'C:/Program Files/nodejs/node.exe'
environment = os.environ.copy()
environment.update({'CI': 'true', 'REACT_APP_STATS_API_PATH': '/stats-api'})
test_settings = {'REACT_APP_STATS_POLL_INTERVAL_MS': '100', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '50'}
build_settings = {'REACT_APP_STATS_POLL_INTERVAL_MS': '250', 'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '1000'}
commands = []


def run(name, arguments, directory, settings):
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        process = subprocess.run(arguments, cwd=directory, env={**environment, **settings}, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    commands.append({'name': name, 'arguments': arguments, 'settings': settings, 'exit': process.returncode})


files = [dashboard / name for name in ['package.json', 'package-lock.json', 'api-server/app.js', 'api-server/server.js', 'api-server/package-lock.json', 'server.js', 'db/index.js']]
for directory, pattern in [('lib', '*.js'), ('test', '*.cjs'), ('wsclient', '*.js'), ('react-frontend/src', '*')]:
    files += [path for path in (dashboard / directory).rglob(pattern) if path.is_file()]
files += [frontend / 'package.json', frontend / 'package-lock.json']
files += [path for path in (frontend / 'public').rglob('*') if path.is_file()]
hashes = {path.relative_to(dashboard).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
tests = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))['scripts']['test'].split()[1:]
run('contracts', [node] + tests, dashboard, {})
run('react-tests', [node, 'node_modules/react-scripts/scripts/test.js', '--watchAll=false', '--runInBand'], frontend, test_settings)
run('build', [node, 'node_modules/react-scripts/scripts/build.js'], frontend, build_settings)
versions = {'node': subprocess.check_output([node, '--version'], text=True).strip()}
for name in ['react', 'react-dom', 'prop-types', 'react-scripts', 'webpack', 'axios', 'jest']:
    versions[name] = json.loads((frontend / 'node_modules' / name / 'package.json').read_text(encoding='utf-8'))['version']
assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
result = {
    'dashboard_directory': str(dashboard), 'versions': versions, 'commands': commands,
    'source_sha256': hashes, 'node_options': environment.get('NODE_OPTIONS'),
    'build_sha256': {path.relative_to(frontend / 'build').as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((frontend / 'build').rglob('*')) if path.is_file()} if commands[-1]['exit'] == 0 else {},
}
(output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
(output / 'run.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'versions': versions, 'exits': {item['name']: item['exit'] for item in commands}}, indent=2))
