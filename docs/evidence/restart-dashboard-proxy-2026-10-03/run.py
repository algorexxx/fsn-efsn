import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
attempt = bundle / sys.argv[1]
attempt.mkdir(exist_ok=False)
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def linux(path):
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(name, args, expected=0, timeout=100):
    started = time.monotonic()
    with (attempt / (name + '.stdout.txt')).open('wb') as output, (attempt / (name + '.stderr.txt')).open('wb') as errors:
        completed = subprocess.run(args, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=output, stderr=errors, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    record['commands'].append({'name': name, 'exit': completed.returncode, 'seconds': time.monotonic() - started})
    assert completed.returncode == expected, name


source = subprocess.check_output(git + ['ls-files', '-co', '--exclude-standard']).decode().splitlines()
record = {'runner_sha256': digest(Path(__file__)), 'dashboard_base': subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip(), 'commands': [], 'source_sha256': {name: digest(dashboard / name) for name in source if not name.endswith('.md')}, 'build_sha256': {path.relative_to(dashboard / 'react-frontend/build').as_posix(): digest(path) for path in (dashboard / 'react-frontend/build').rglob('*') if path.is_file()}, 'runtime_sha256': {name: digest(root / name) for name in ['tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node', 'tmp/dashboard-proxy-runtime/extracted/usr/sbin/nginx', 'tmp/dashboard-proxy-runtime/nginx_1.24.0-2ubuntu7.18_amd64.deb']}, 'dependency_sha256': {name: digest(dashboard / name) for name in ['node_modules/ws/lib/WebSocket.js', 'node_modules/forwarded-for/index.js', 'node_modules/primus/middleware/forwarded.js']}, 'passed': False}
private = subprocess.check_output(wsl + ['mktemp', '-d', '/tmp/fusion-dashboard-proxy-XXXXXXXX']).decode().strip()
record['private_directory'] = private
node = linux(root / 'tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node')
nginx = linux(root / 'tmp/dashboard-proxy-runtime/extracted/usr/sbin/nginx')
try:
    command('runtime', wsl + [nginx, '-V'])
    command('node', wsl + [node, '--version'])
    command('libraries', wsl + ['ldd', nginx])
    command('package', wsl + ['apt-cache', 'show', 'nginx=1.24.0-2ubuntu7.18'])
    command('openssl', wsl + ['openssl', 'version', '-a'])
    command('ca', wsl + ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2', '-subj', '/CN=Fusion local proxy test CA', '-addext', 'basicConstraints=critical,CA:TRUE', '-keyout', private + '/ca.key', '-out', private + '/ca.crt'])
    command('csr', wsl + ['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-subj', '/CN=dashboard.test', '-addext', 'subjectAltName=DNS:dashboard.test,IP:127.0.0.1', '-keyout', private + '/server.key', '-out', private + '/server.csr'])
    command('certificate', wsl + ['openssl', 'x509', '-req', '-in', private + '/server.csr', '-CA', private + '/ca.crt', '-CAkey', private + '/ca.key', '-set_serial', '1', '-days', '2', '-copy_extensions', 'copy', '-out', private + '/server.crt'])
    command('public-certificates', wsl + ['cp', private + '/ca.crt', private + '/server.crt', linux(attempt)])
    environment = ['env', 'TEST_NGINX=' + nginx, 'TEST_TLS_CA=' + private + '/ca.crt', 'TEST_TLS_CERT=' + private + '/server.crt', 'TEST_TLS_KEY=' + private + '/server.key', 'DASHBOARD_PROXY_EVIDENCE=' + linux(attempt)]
    command('syntax', wsl + [node, '--check', linux(dashboard / 'test/proxy-tls.test.cjs')])
    command('proxy-test', wsl + environment + [node, '--test', linux(dashboard / 'test/proxy-tls.test.cjs')])
    package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
    wire = package['scripts']['test:wire'].split()[1:]
    command('wire-tests', wsl + [node] + wire)
    record['passed'] = True
finally:
    command('private-cleanup', wsl + ['rm', '-f', private + '/ca.key', private + '/ca.crt', private + '/server.key', private + '/server.crt', private + '/server.csr'])
    command('private-directory-cleanup', wsl + ['rmdir', private])
    record['private_removed'] = subprocess.run(wsl + ['test', '!', '-e', private], creationflags=subprocess.CREATE_NO_WINDOW).returncode == 0
    (attempt / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'passed': record['passed'], 'private_removed': record['private_removed'], 'attempt': str(attempt)}), flush=True)
