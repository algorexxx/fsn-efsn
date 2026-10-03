import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
attempt, mode = sys.argv[1:]
assert re.fullmatch(r'attempt-[1-9][0-9]*', attempt)
assert mode in ['small-snapshot', 'small-output', 'aligned', 'persistence', 'enrollment']
output = bundle / attempt
output.mkdir()
(output / 'run.py').write_bytes(Path(__file__).read_bytes())
sources = set(subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=dashboard).decode().splitlines())
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(sources)}
scratch = root / 'tmp' / ('dashboard-profile-postgres-' + secrets.token_hex(6))
scratch.mkdir()
data = scratch / 'data'
password = secrets.token_hex(24)
password_file = scratch / 'password.txt'
password_file.write_bytes(password.encode('utf-8'))
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
environment = {**os.environ, 'TEST_PG_PORT': str(port), 'TEST_PG_PASSWORD_FILE': str(password_file), 'PGPASSWORD': password, 'DASHBOARD_PROFILE': mode, 'DASHBOARD_PROFILE_EVIDENCE': str(output)}
postgres = Path('C:/Program Files/PostgreSQL/18/bin')
node = 'C:/Program Files/nodejs/node.exe'
commands = []


def run(name, command, timeout=45):
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run([str(item) for item in command], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    commands.append({'name': name, 'command': [str(item) for item in command], 'exit_code': result.returncode})
    print(name, 'exit', result.returncode, flush=True)
    return result.returncode


started = False
success = False
try:
    assert run('initdb', [postgres / 'initdb.exe', '-D', data, '-U', 'dashboard_test_admin', '-A', 'scram-sha-256', '--pwfile', password_file, '--encoding=UTF8', '--locale=C']) == 0
    started = run('start', [postgres / 'pg_ctl.exe', '-D', data, '-l', scratch / 'postgres.log', '-o', f'-h 127.0.0.1 -p {port} -c shared_buffers=16MB -c max_connections=10', '-w', 'start']) == 0
    assert started
    success = run('profile', [node, '--test', '--test-reporter=tap', 'test/persistence.test.cjs' if mode == 'persistence' else 'test/enrollment-profile.test.cjs' if mode == 'enrollment' else 'test/dashboard-profile.test.cjs'], timeout=55) == 0
finally:
    if started:
        stopped = run('stop', [postgres / 'pg_ctl.exe', '-D', data, '-m', 'fast', '-w', 'stop'])
        status = run('stopped-status', [postgres / 'pg_ctl.exe', '-D', data, 'status'])
        success = success and stopped == 0 and status == 3
    password_file.unlink()
    if (scratch / 'postgres.log').exists():
        (output / 'postgres.log').write_bytes((scratch / 'postgres.log').read_bytes())
    assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == value for name, value in hashes.items())
    result = {'mode': mode, 'expected_outcome_passed': success, 'scratch_directory': str(scratch), 'password_removed': not password_file.exists(), 'source_sha256': hashes, 'commands': commands, 'node': subprocess.check_output([node, '--version']).decode().strip(), 'postgres': subprocess.check_output([str(postgres / 'postgres.exe'), '--version']).decode().strip(), 'scope': 'One disposable loopback database and bounded synthetic telemetry fixture; no real blockchain, key or external endpoint.'}
    (output / 'result.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
sys.exit(0 if success else 1)
