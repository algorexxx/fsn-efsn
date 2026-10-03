import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
dashboard = workspace / 'tmp/fsn-stats-auth'
postgres = Path('C:/Program Files/PostgreSQL/18/bin')
attempt = sys.argv[1]
mode = sys.argv[2]
assert mode in ['actual-efsn', 'persistence']
if not re.fullmatch(r'attempt-[1-9][0-9]*', attempt):
    raise ValueError('Use an unused attempt-N and actual-efsn/persistence')
output = evidence / attempt
output.mkdir()

binary = workspace / 'tmp/dashboard-presentation-tests'
source_files = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=workspace).decode().splitlines()
source_hashes = {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest() for name in sorted(set(source_files)) if name.endswith('.go') or name in ['go.mod', 'go.sum']}
(output / 'efsn-source-sha256.json').write_bytes((json.dumps(source_hashes, indent=2) + '\n').encode('utf-8'))
(output / 'run.py').write_bytes(Path(__file__).read_bytes())
scratch = workspace / 'tmp' / ('dashboard-postgres-' + secrets.token_hex(6))
scratch.mkdir()
data = scratch / 'data'
password = secrets.token_hex(24)
password_file = scratch / 'password.txt'
password_file.write_text(password, encoding='utf-8')
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
environment = dict(os.environ, TEST_PG_PORT=str(port), TEST_PG_PASSWORD=password, TEST_PG_PASSWORD_FILE=str(password_file), PGPASSWORD=password, EFSN_TELEMETRY_BINARY=str(binary), EFSN_TELEMETRY_EVIDENCE=str(output), EFSN_BROWSER_MODULE='C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright', EFSN_LINUX_NODE=str(workspace / 'tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node'))
commands = []


def run(name, command, cwd=dashboard, timeout=45):
    with (output / (name + '.txt')).open('wb') as stdout, (output / (name + '-stderr.txt')).open('wb') as stderr:
        result = subprocess.run([str(item) for item in command], cwd=cwd, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    result.stdout = (output / (name + '.txt')).read_bytes()
    result.stderr = (output / (name + '-stderr.txt')).read_bytes()
    commands.append({'name': name, 'command': [str(item) for item in command], 'exit': result.returncode})
    print(name, 'exit', result.returncode, flush=True)
    return result


sources = sorted(set(subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=dashboard).decode().splitlines()))
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sources}
build = dashboard / 'react-frontend/build'
build_hashes = {str(path.relative_to(build)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(build.rglob('*')) if path.is_file()}
if 'index.html' not in build_hashes:
    raise ValueError('Compile the dashboard before the integration run')
initialized = run('initdb', [postgres / 'initdb.exe', '-D', data, '-U', 'dashboard_test_admin', '-A', 'scram-sha-256', '--pwfile', password_file, '--encoding=UTF8', '--locale=C'])
started = False
success = False
try:
    if initialized.returncode:
        raise RuntimeError('Disposable cluster initialization failed')
    start = run('start', [postgres / 'pg_ctl.exe', '-D', data, '-l', scratch / 'postgres.log', '-o', f'-h 127.0.0.1 -p {port} -c shared_buffers=16MB -c max_connections=10', '-w', 'start'])
    started = start.returncode == 0
    if not started:
        raise RuntimeError('Disposable cluster startup failed')
    control = run('psql-control', [postgres / 'psql.exe', '-h', '127.0.0.1', '-p', str(port), '-U', 'dashboard_test_admin', '-d', 'postgres', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-c', 'SELECT 42::integer'])
    persistence = run('persistence', ['C:/Program Files/nodejs/node.exe', '--test', '--test-reporter=tap', 'test/efsn-telemetry.test.cjs' if mode == 'actual-efsn' else 'test/persistence.test.cjs'], timeout=80)
    success = control.returncode == 0 and control.stdout.strip() == b'42' and all(item.returncode == 0 for item in [persistence])
finally:
    if started:
        stop = run('stop', [postgres / 'pg_ctl.exe', '-D', data, '-m', 'fast', '-w', 'stop'])
        status = run('stopped-status', [postgres / 'pg_ctl.exe', '-D', data, 'status'])
        success = success and stop.returncode == 0 and status.returncode in [1, 3] and b'no server running' in status.stdout + status.stderr
    if (scratch / 'postgres.log').exists():
        (output / 'postgres.log').write_bytes((scratch / 'postgres.log').read_bytes())
    password_file.unlink()
    assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    assert all(hashlib.sha256((build / name).read_bytes()).hexdigest() == digest for name, digest in build_hashes.items())
    summary = {
        'mode': mode, 'dashboard_directory': str(dashboard), 'scratch_directory': str(scratch),
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'source_sha256': hashes, 'build_sha256': build_hashes, 'commands': commands, 'expected_outcome_passed': success,
        'node': subprocess.check_output(['C:/Program Files/nodejs/node.exe', '--version'], text=True).strip(),
        'pg': json.loads((dashboard / 'node_modules/pg/package.json').read_text(encoding='utf-8'))['version'],
        'postgres': subprocess.check_output([str(postgres / 'postgres.exe'), '--version'], text=True).strip(),
        'password_file_removed': not password_file.exists(),
        'scope': 'Disposable new SCRAM-authenticated loopback-only PostgreSQL cluster; no existing database accessed. Cluster stopped and data retained in ignored scratch directory.',
    }
    (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: summary[key] for key in ['mode', 'expected_outcome_passed', 'node', 'pg', 'postgres', 'password_file_removed']}, indent=2))
sys.exit(0 if success else 1)
