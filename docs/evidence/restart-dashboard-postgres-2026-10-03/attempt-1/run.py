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
attempt, mode = sys.argv[1:]
if not re.fullmatch(r'attempt-[1-9][0-9]*', attempt) or mode not in ['baseline', 'candidate']:
    raise ValueError('Use an unused attempt-N and baseline/candidate')
output = evidence / attempt
output.mkdir()
(output / 'run.py').write_bytes(Path(__file__).read_bytes())
(output / 'probe.cjs').write_bytes((evidence / 'probe.cjs').read_bytes())
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
    result = subprocess.run([str(item) for item in command], cwd=cwd, env=environment, capture_output=True, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    (output / (name + '.txt')).write_bytes(result.stdout)
    (output / (name + '-stderr.txt')).write_bytes(result.stderr)
    commands.append({'name': name, 'command': [str(item) for item in command], 'exit': result.returncode})
    print(name, 'exit', result.returncode, flush=True)
    return result


sources = ['package.json', 'package-lock.json', 'db/index.js', 'lib/deployment-config.js', 'test/deployment-config.test.cjs', 'test/deployment-wiring.test.cjs']
if (dashboard / 'test/postgres.test.cjs').exists():
    sources.append('test/postgres.test.cjs')
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
    probe = run('driver-probe', ['node', evidence / 'probe.cjs'], timeout=10)
    expected = probe.returncode == (1 if mode == 'baseline' else 0)
    success = control.returncode == 0 and control.stdout.strip() == b'42' and expected
    if mode == 'candidate':
        suite = run('postgres-tests', ['node', '--test', '--test-reporter=tap', 'test/postgres.test.cjs'], timeout=30)
        contracts = run('contracts', ['npm.cmd', 'test'], timeout=45)
        wire = run('wire', ['npm.cmd', 'run', 'test:wire'], timeout=30)
        success = success and all(item.returncode == 0 for item in [suite, contracts, wire])
finally:
    if started:
        stop = run('stop', [postgres / 'pg_ctl.exe', '-D', data, '-m', 'fast', '-w', 'stop'])
        status = run('stopped-status', [postgres / 'pg_ctl.exe', '-D', data, 'status'])
        success = success and stop.returncode == 0 and status.returncode == 3
    if (scratch / 'postgres.log').exists():
        (output / 'postgres.log').write_bytes((scratch / 'postgres.log').read_bytes())
    password_file.unlink()
    assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    summary = {
        'mode': mode, 'dashboard_directory': str(dashboard), 'scratch_directory': str(scratch),
        'source_sha256': hashes, 'commands': commands, 'expected_outcome_passed': success,
        'node': subprocess.check_output(['node', '--version'], text=True).strip(),
        'pg': json.loads((dashboard / 'node_modules/pg/package.json').read_text(encoding='utf-8'))['version'],
        'postgres': subprocess.check_output([str(postgres / 'postgres.exe'), '--version'], text=True).strip(),
        'password_file_removed': not password_file.exists(),
        'scope': 'Disposable new SCRAM-authenticated loopback-only PostgreSQL cluster; no existing database accessed. Cluster stopped and data retained in ignored scratch directory.',
    }
    (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: summary[key] for key in ['mode', 'expected_outcome_passed', 'node', 'pg', 'postgres', 'password_file_removed']}, indent=2))
sys.exit(0 if success else 1)
