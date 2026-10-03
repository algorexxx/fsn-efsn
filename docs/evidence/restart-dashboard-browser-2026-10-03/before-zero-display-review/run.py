import hashlib
import json
import os
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
dashboard = workspace / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
node = 'C:/Program Files/nodejs/node.exe'
npm = 'C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js'
environment = os.environ.copy()
settings = {
    'CI': 'true',
    'REACT_APP_STATS_API_PATH': '/stats-api',
    'REACT_APP_STATS_POLL_INTERVAL_MS': '100',
    'REACT_APP_STATS_REQUEST_TIMEOUT_MS': '50',
}
environment.update(settings)
commands = []


def run(name, arguments, directory):
    with (evidence / (name + '.stdout.txt')).open('wb') as output, (evidence / (name + '.stderr.txt')).open('wb') as errors:
        process = subprocess.run(arguments, cwd=directory, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=errors, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    commands.append({'name': name, 'arguments': arguments, 'directory': str(directory), 'exit': process.returncode})


files = [dashboard / name for name in ['package.json', 'package-lock.json', 'api-server/app.js', 'api-server/server.js', 'api-server/package-lock.json', 'server.js', 'db/index.js']]
files += list((dashboard / 'lib').rglob('*.js'))
files += list((dashboard / 'test').rglob('*.cjs'))
files += list((dashboard / 'wsclient').glob('*.js'))
files += list((frontend / 'src').rglob('*.js'))
files += [frontend / 'package.json', frontend / 'package-lock.json']
hashes = {path.relative_to(dashboard).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
tests = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))['scripts']['test'].split()[1:]
run('contracts', [node] + tests, dashboard)
run('react-tests', [node, 'node_modules/react-scripts/scripts/test.js', '--watchAll=false', '--runInBand'], frontend)
run('build', [node, 'node_modules/react-scripts/scripts/build.js'], frontend)
versions = {
    'node': subprocess.check_output([node, '--version'], text=True).strip(),
    'npm': subprocess.check_output([node, npm, '--version'], text=True).strip(),
}
for name in ['react', 'react-dom', 'react-scripts', 'webpack', 'axios', 'jest']:
    versions[name] = json.loads((frontend / 'node_modules' / name / 'package.json').read_text(encoding='utf-8'))['version']
assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
result = {
    'dashboard_directory': str(dashboard),
    'base': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD'], text=True).strip(),
    'settings': settings, 'versions': versions, 'commands': commands, 'source_sha256': hashes,
    'tests_passed': commands[0]['exit'] == 0 and commands[1]['exit'] == 0,
    'build_passed': commands[2]['exit'] == 0,
    'node_options': environment.get('NODE_OPTIONS'),
}
(evidence / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ['versions', 'tests_passed', 'build_passed', 'node_options']}, indent=2))
