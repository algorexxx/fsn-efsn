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
mode = 'candidate'
if not re.fullmatch(r'attempt-[1-9][0-9]*', attempt) or mode not in ['baseline', 'candidate']:
    raise ValueError('Use an unused attempt-N and baseline/candidate')
output = evidence / attempt
output.mkdir()
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
environment = dict(os.environ, TEST_PG_PORT=str(port), TEST_PG_PASSWORD=password, TEST_PG_PASSWORD_FILE=str(password_file), PGPASSWORD=password)
commands = []


def run(name, command, cwd=dashboard, timeout=45):
    with (output / (name + '.txt')).open('wb') as stdout, (output / (name + '-stderr.txt')).open('wb') as stderr:
        result = subprocess.run([str(item) for item in command], cwd=cwd, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    result.stdout = (output / (name + '.txt')).read_bytes()
    result.stderr = (output / (name + '-stderr.txt')).read_bytes()
    commands.append({'name': name, 'command': [str(item) for item in command], 'exit': result.returncode})
    print(name, 'exit', result.returncode, flush=True)
    return result


sources = [
    'package.json', 'package-lock.json', 'db/index.js', 'lib/deployment-config.js',
    'db_methods/populate.js', 'db_methods/retrieve.js', 'db/schema/001-dashboard.sql',
    'wsclient/wsclient.js', 'wsclient/collect-snapshots.js', 'api-server/server.js', 'api-server/app.js',
    'test/collector.test.cjs', 'test/telemetry-credentials.test.cjs', 'test/deployment-config.test.cjs',
    'test/deployment-wiring.test.cjs', 'test/snapshot-collector.test.cjs', 'test/snapshot-api.test.cjs',
    'test/postgres.test.cjs', 'test/persistence.test.cjs', 'test/telemetry-wire.test.cjs',
    'test/fixtures/collector.cjs', 'test/fixtures/wire-client.cjs', 'test/fixtures/wire-server.cjs', 'test/fixtures/http.cjs',
    'lib/collector-output.js', 'test/fixtures/collector-environment.cjs',
    'server.js', 'lib/node.js', 'lib/collection.js', 'lib/history.js', 'lib/telemetry-report.js', 'api-server/report-freshness.js',
]
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sources}
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
    persistence = run('persistence', ['C:/Program Files/nodejs/node.exe', '--test', '--test-reporter=tap', 'test/persistence.test.cjs'], timeout=55)
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
    summary = {
        'mode': mode, 'dashboard_directory': str(dashboard), 'scratch_directory': str(scratch),
        'source_sha256': hashes, 'commands': commands, 'expected_outcome_passed': success,
        'node': subprocess.check_output(['C:/Program Files/nodejs/node.exe', '--version'], text=True).strip(),
        'pg': json.loads((dashboard / 'node_modules/pg/package.json').read_text(encoding='utf-8'))['version'],
        'postgres': subprocess.check_output([str(postgres / 'postgres.exe'), '--version'], text=True).strip(),
        'password_file_removed': not password_file.exists(),
        'scope': 'Disposable new SCRAM-authenticated loopback-only PostgreSQL cluster; no existing database accessed. Cluster stopped and data retained in ignored scratch directory.',
    }
    (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: summary[key] for key in ['mode', 'expected_outcome_passed', 'node', 'pg', 'postgres', 'password_file_removed']}, indent=2))
sys.exit(0 if success else 1)
