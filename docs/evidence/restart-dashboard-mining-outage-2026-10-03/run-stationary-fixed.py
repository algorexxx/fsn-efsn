import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
assert re.fullmatch(r'stationary-[1-9][0-9]*', sys.argv[1])
output = bundle / sys.argv[1]
output.mkdir(exist_ok=False)
scratch = root / 'tmp' / ('dashboard-tls-' + secrets.token_hex(6))
scratch.mkdir()
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
private = subprocess.check_output(wsl + ['mktemp', '-d', '/home/rehearsal/fusion-dashboard-tls-XXXXXXXX']).decode().strip()
password_file = scratch / 'password.txt'
password = secrets.token_hex(24)
password_file.write_text(password, encoding='utf-8')
port = int(subprocess.check_output(wsl + ['python3', '-c', 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()']).decode())
record = {'commands': [], 'passed': False, 'scratch_directory': str(scratch), 'linux_scratch': private}
environment = dict(os.environ)
started = False


def linux(path):
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, args, timeout=45, expected=0):
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run([str(value) for value in args], cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    record['commands'].append({'name': name, 'exit': result.returncode})
    print(name, result.returncode, flush=True)
    assert result.returncode == expected, name
    return (output / (name + '.stdout.txt')).read_bytes()


def sources(directory, go_only=False):
    names = subprocess.check_output(['git', '-C', str(directory), '-c', 'core.autocrlf=false', 'ls-files', '-co', '--exclude-standard']).decode().splitlines()
    selected = [name for name in sorted(set(names)) if name.endswith('.go') or name in ['go.mod', 'go.sum']] if go_only else [name for name in sorted(set(names)) if not name.endswith('.md')]
    return {name: digest(directory / name) for name in selected}


pg_root = root / 'tmp/dashboard-postgres-linux-runtime/extracted'
pg_bin = linux(pg_root / 'usr/lib/postgresql/16/bin')
pg_environment = wsl + ['env', 'LD_LIBRARY_PATH=' + linux(pg_root / 'usr/lib/x86_64-linux-gnu')]
binary = root / 'tmp/dashboard-mining-fixed-tests'
record['source_sha256'] = sources(dashboard)
record['efsn_source_sha256'] = sources(root, go_only=True)
build = dashboard / 'react-frontend/build'
record['build_sha256'] = {path.relative_to(build).as_posix(): digest(path) for path in build.rglob('*') if path.is_file()}
record['runner_sha256'] = digest(Path(__file__))
runtime = ['tmp/dashboard-mining-fixed-tests', 'tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node', 'tmp/dashboard-proxy-runtime/extracted/usr/sbin/nginx']
runtime += [(path.relative_to(root)).as_posix() for path in (root / 'tmp/dashboard-postgres-linux-runtime').glob('*.deb')]
runtime += ['tmp/dashboard-postgres-linux-runtime/extracted/usr/lib/postgresql/16/bin/' + name for name in ['postgres', 'pg_ctl', 'psql', 'initdb']]
record['runtime_sha256'] = {name: digest(root / name) for name in runtime}
record['windows_node_sha256'] = digest(Path('C:/Program Files/nodejs/node.exe'))
record['playwright_version'] = json.loads(Path('C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json').read_text(encoding='utf-8'))['version']
try:
    run('postgres-version', pg_environment + [pg_bin + '/postgres', '--version'])
    run('nginx-version', wsl + [linux(root / runtime[2]), '-V'])
    run('node-version', ['C:/Program Files/nodejs/node.exe', '--version'])
    run('openssl-version', wsl + ['openssl', 'version', '-a'])
    run('ca', wsl + ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2', '-subj', '/CN=Fusion actual WSS test CA', '-addext', 'basicConstraints=critical,CA:TRUE', '-keyout', private + '/ca.key', '-out', private + '/ca.crt'])
    run('csr', wsl + ['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-subj', '/CN=127.0.0.1', '-addext', 'subjectAltName=IP:127.0.0.1', '-keyout', private + '/server.key', '-out', private + '/server.csr'])
    run('certificate', wsl + ['openssl', 'x509', '-req', '-in', private + '/server.csr', '-CA', private + '/ca.crt', '-CAkey', private + '/ca.key', '-set_serial', '1', '-days', '2', '-copy_extensions', 'copy', '-out', private + '/server.crt'])
    run('public-certificates', wsl + ['cp', private + '/ca.crt', private + '/server.crt', linux(output)])
    run('public-key', wsl + ['openssl', 'x509', '-in', private + '/server.crt', '-pubkey', '-noout', '-out', private + '/public.pem'])
    der = run('spki', wsl + ['openssl', 'pkey', '-pubin', '-in', private + '/public.pem', '-outform', 'DER'])
    record['certificate_spki'] = base64.b64encode(hashlib.sha256(der).digest()).decode()
    run('initdb', pg_environment + [pg_bin + '/initdb', '-D', private + '/data', '-L', linux(pg_root / 'usr/share/postgresql/16'), '-U', 'dashboard_test_admin', '-A', 'scram-sha-256', '--pwfile', linux(password_file), '--encoding=UTF8', '--locale=C'])
    run('start', pg_environment + [pg_bin + '/pg_ctl', '-D', private + '/data', '-l', private + '/postgres.log', '-o', f'-h 127.0.0.1 -p {port} -k {private} -c shared_buffers=16MB -c max_connections=16 -c jit=off', '-w', 'start'])
    started = True
    pgpass = f'127.0.0.1:{port}:postgres:dashboard_test_admin:{password}\n'.encode()
    write = subprocess.run(wsl + ['python3', '-c', 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); p.write_bytes(sys.stdin.buffer.read()); p.chmod(0o600)', private + '/pgpass'], input=pgpass, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    assert write.returncode == 0
    control = run('control', pg_environment + ['PGPASSFILE=' + private + '/pgpass', pg_bin + '/psql', '-h', '127.0.0.1', '-p', str(port), '-U', 'dashboard_test_admin', '-d', 'postgres', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-c', 'SELECT 42::integer'])
    assert control.strip() == b'42'
    environment.update(TEST_PG_PORT=str(port), TEST_PG_PASSWORD_FILE=str(password_file), EFSN_TELEMETRY_BINARY=str(binary), EFSN_TELEMETRY_EVIDENCE=str(output), EFSN_BROWSER_MODULE='C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright', EFSN_LINUX_NODE=str(root / 'tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node'), EFSN_TLS_CA=str(output / 'ca.crt'), EFSN_TLS_CERT=str(output / 'server.crt'), EFSN_TLS_KEY=private + '/server.key', EFSN_TLS_OUTPUT=str(output / 'proxy'), TEST_NGINX=str(root / runtime[2]), EFSN_TLS_SPKI=record['certificate_spki'])
    run('syntax', ['C:/Program Files/nodejs/node.exe', '--check', 'test/efsn-telemetry.test.cjs'])
    run('actual-wss', ['C:/Program Files/nodejs/node.exe', '--test', '--test-reporter=tap', 'test/efsn-telemetry.test.cjs'], timeout=85)
    record['passed'] = True
finally:
    if started:
        run('stop', pg_environment + [pg_bin + '/pg_ctl', '-D', private + '/data', '-m', 'fast', '-w', 'stop'])
        run('stopped-status', pg_environment + [pg_bin + '/pg_ctl', '-D', private + '/data', 'status'], expected=3)
        run('postgres-log', wsl + ['cp', private + '/postgres.log', linux(output / 'postgres.log')])
    private_names = ['ca.key', 'ca.crt', 'server.key', 'server.crt', 'server.csr', 'public.pem', 'pgpass']
    run('private-cleanup', wsl + ['rm', '-f'] + [private + '/' + name for name in private_names])
    password_file.unlink()
    record['password_removed'] = not password_file.exists()
    checks = subprocess.check_output(wsl + ['python3', '-c', 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(json.dumps({"private_removed":all(not (p/name).exists() for name in sys.argv[2:]),"postgres_pid_absent":not (p/"data/postmaster.pid").exists()}))', private] + private_names)
    record.update(json.loads(checks))
    record['sources_unchanged_during_run'] = all(digest(dashboard / name) == value for name, value in record['source_sha256'].items())
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: record[key] for key in ['passed', 'password_removed', 'private_removed', 'postgres_pid_absent', 'sources_unchanged_during_run']}), flush=True)
