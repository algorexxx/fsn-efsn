import gzip
import hashlib
import http.client
import json
import os
import re
import secrets
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import time
import traceback
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
assert os.geteuid() == 0 and re.fullmatch(r'run-[1-9][0-9]*', sys.argv[1])
output = bundle / sys.argv[1]
output.mkdir(exist_ok=False)
for name in ['run-linux.py', 'backend.cjs', 'reporter.cjs']:
    shutil.copyfile(bundle / name, output / name)
prefix = 'fsn-proxy-test-' + secrets.token_hex(4)
private = Path('/run') / (prefix + '-fixture')
runtime = Path('/run') / (prefix + '-runtime')
logs = Path('/var/log') / (prefix + '-logs')
state = Path('/var/lib') / (prefix + '-rotate')
private.mkdir(mode=0o750)
os.chown(private, 0, 1000)
backend_dir = private / 'backend'
backend_dir.mkdir(mode=0o700)
os.chown(backend_dir, 1000, 1000)
units = {'proxy': prefix + '.service', 'rotate': prefix + '-rotate.service', 'timer': prefix + '-rotate.timer'}
node = root / 'tmp/dashboard-runtime-review/v24.21.0/node'
nginx = root / 'tmp/dashboard-proxy-runtime/extracted/usr/sbin/nginx'
installed = []
processes = []
files = []
record = {'passed': False, 'prefix': prefix, 'units': units, 'commands': [], 'checkpoints': [], 'source_sha256': {}}
secret = secrets.token_hex(24)


def write(path, text, mode=0o644, owner=0, group=0):
    path.write_text(text, encoding='utf-8', newline='\n')
    path.chmod(mode)
    os.chown(path, owner, group)


def run(name, command, expected=0, timeout=30, save=True):
    result = subprocess.run([str(value) for value in command], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if save:
        (output / (name + '.stdout.txt')).write_bytes(result.stdout)
        (output / (name + '.stderr.txt')).write_bytes(result.stderr)
        record['commands'].append({'name': name, 'exit': result.returncode})
    if expected is not None:
        assert result.returncode == expected, (name, result.returncode, result.stderr.decode(errors='replace'))
    return result


def control(*args, expected=0, save=True):
    return run('control-' + str(len(record['commands'])), ['systemctl', *args], expected=expected, save=save)


def status(unit):
    text = control('show', unit, '-p', 'MainPID', '-p', 'ActiveState', '-p', 'SubState', '-p', 'NRestarts', '-p', 'ExecMainStatus', '-p', 'Result', '-p', 'ControlGroup', save=False).stdout.decode()
    return dict(line.split('=', 1) for line in text.splitlines())


def wait(check, label, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError('Deadline: ' + label)


def checkpoint(name, values):
    record['checkpoints'].append({'name': name, **values})
    print(name, json.dumps(values), flush=True)


def request(path='/'):
    connection = http.client.HTTPSConnection('127.0.0.1', port, context=ssl.create_default_context(cafile=str(private / 'ca.crt')), timeout=5)
    try:
        connection.connect()
        serial = connection.sock.getpeercert()['serialNumber']
        connection.request('GET', path, headers={'Host': 'dashboard.test'})
        response = connection.getresponse()
        return {'status': response.status, 'serial': serial, 'body': response.read()}
    except (OSError, http.client.HTTPException):
        return {'status': 0}
    finally:
        connection.close()


def fresh():
    response = request('/stats-api/nodes')
    if response['status'] != 200:
        return False
    rows = json.loads(response['body'])
    return len(rows) == 1 and rows[0]['id'] == 'proxy-node' and rows[0]['block'] == 901 and rows[0]['reportValidForMs']['block'] > 0


def events():
    if not (output / 'reporter.log').exists():
        return []
    return [json.loads(line) for line in (output / 'reporter.log').read_text(encoding='utf-8').splitlines() if line.startswith('{') and line.endswith('}')]


def connects():
    return sum(item['event'] == 'connected' for item in events())


def children(pid):
    path = Path('/proc') / str(pid) / 'task' / str(pid) / 'children'
    return [int(value) for value in path.read_text().split()] if path.exists() else []


def log_descriptors(pids):
    descriptors = []
    for pid in pids:
        for fd in (Path('/proc') / str(pid) / 'fd').iterdir():
            try:
                target = os.readlink(fd)
                if target.startswith(str(logs) + '/'):
                    descriptors.append({'pid': pid, 'target': target, 'inode': fd.stat().st_ino})
            except FileNotFoundError:
                pass
    return descriptors


def reopened(pids):
    active = {str(logs / name): (logs / name).stat().st_ino for name in ['nginx-access.log', 'nginx-error.log']}
    descriptors = log_descriptors(pids)
    return descriptors if descriptors and all(item['inode'] == active.get(item['target']) for item in descriptors) else False


def select_certificate(name):
    link = private / 'current.new'
    link.symlink_to(private / name, target_is_directory=True)
    link.replace(private / 'current')


def install_unit(name, source_name, replacements):
    source = dashboard / 'deploy/systemd' / source_name
    record['source_sha256'][source.relative_to(dashboard).as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
    content = source.read_text(encoding='utf-8')
    for old, new in replacements.items():
        assert old in content, old
        content = content.replace(old, str(new))
    destination = Path('/run/systemd/system') / name
    assert not destination.exists()
    write(destination, content)
    write(output / name, content)
    installed.append(destination)


with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
record['port'] = port
try:
    run('nginx-version', [nginx, '-V'])
    run('logrotate-version', ['/usr/sbin/logrotate', '--version'])
    run('systemd-version', ['systemctl', '--version'])
    run('calendar', ['systemd-analyze', 'calendar', '*-*-* *:00/5:00'])
    for name in ['backend.cjs', 'reporter.cjs']:
        run('syntax-' + name, [node, '--check', bundle / name])
    run('ca', ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2', '-subj', '/CN=Fusion proxy lifecycle fixture CA', '-addext', 'basicConstraints=critical,CA:TRUE', '-keyout', private / 'ca.key', '-out', private / 'ca.crt'])
    for serial in [1, 2]:
        directory = private / ('certificate-' + str(serial))
        directory.mkdir(mode=0o750)
        os.chown(directory, 0, 1000)
        run('csr-' + str(serial), ['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-nodes', '-subj', '/CN=dashboard.test', '-addext', 'subjectAltName=DNS:dashboard.test,IP:127.0.0.1', '-keyout', directory / 'key.pem', '-out', directory / 'request.csr'])
        run('cert-' + str(serial), ['openssl', 'x509', '-req', '-in', directory / 'request.csr', '-CA', private / 'ca.crt', '-CAkey', private / 'ca.key', '-set_serial', str(serial), '-days', '2', '-copy_extensions', 'copy', '-out', directory / 'cert.pem'])
        (directory / 'key.pem').chmod(0o640)
        os.chown(directory / 'key.pem', 0, 1000)
        shutil.copyfile(directory / 'cert.pem', output / ('certificate-' + str(serial) + '.pem'))
    shutil.copyfile(private / 'ca.crt', output / 'ca.crt')
    select_certificate('certificate-1')
    write(backend_dir / 'telemetry.json', json.dumps({'proxy-node': secret}), 0o600, 1000, 1000)
    backend_log = (output / 'backend.log').open('wb')
    files.append(backend_log)
    backend = subprocess.Popen(['runuser', '-u', 'rehearsal', '--', str(node), str(bundle / 'backend.cjs'), str(dashboard), str(backend_dir)], stdout=backend_log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(backend)
    wait(lambda: (backend_dir / 'ready.json').exists(), 'backend ready')
    ready = json.loads((backend_dir / 'ready.json').read_text())
    values = {'RUN': runtime, 'LOG': logs, 'HOST': 'dashboard.test', 'TLS_PORT': port, 'CERT': private / 'current/cert.pem', 'KEY': private / 'current/key.pem', 'BUILD': dashboard / 'react-frontend/build', 'COLLECTOR_PORT': ready['collector'], 'API_PORT': ready['api']}
    source = dashboard / 'deploy/nginx.conf.template'
    record['source_sha256']['deploy/nginx.conf.template'] = hashlib.sha256(source.read_bytes()).hexdigest()
    config = re.sub(r'@@([A-Z_]+)@@', lambda match: str(values[match.group(1)]), source.read_text(encoding='utf-8'))
    write(private / 'nginx.conf', config, 0o640, 0, 1000)
    write(output / 'nginx.conf', config)
    install_unit(units['proxy'], 'fsn-stats-proxy.service', {'User=fsn-stats-proxy': 'User=rehearsal', 'Group=fsn-stats-proxy': 'Group=rehearsal', 'RuntimeDirectory=fsn-stats-proxy': 'RuntimeDirectory=' + runtime.name, 'LogsDirectory=fsn-stats-proxy': 'LogsDirectory=' + logs.name, '/usr/sbin/nginx': nginx, '/etc/fsn-stats/nginx.conf': private / 'nginx.conf', 'LogNamespace=fsn-stats': 'LogNamespace=' + prefix})
    install_unit(units['rotate'], 'fsn-stats-logrotate.service', {'/var/lib/fsn-stats-logrotate/status': state / 'status', '/etc/fsn-stats/logrotate.conf': private / 'logrotate.conf', 'StateDirectory=fsn-stats-logrotate': 'StateDirectory=' + state.name, '/var/log/fsn-stats-proxy': logs, 'LogNamespace=fsn-stats': 'LogNamespace=' + prefix})
    install_unit(units['timer'], 'fsn-stats-logrotate.timer', {'Unit=fsn-stats-logrotate.service': 'Unit=' + units['rotate']})
    journal_source = dashboard / 'deploy/systemd/journald@fsn-stats.conf'
    journal_path = Path('/run/systemd') / ('journald@' + prefix + '.conf.d') / '50-test.conf'
    journal_path.parent.mkdir()
    write(journal_path, journal_source.read_text(encoding='utf-8').replace('Storage=persistent', 'Storage=volatile'))
    installed.append(journal_path)
    source = dashboard / 'deploy/logrotate.conf'
    record['source_sha256']['deploy/logrotate.conf'] = hashlib.sha256(source.read_bytes()).hexdigest()
    rotation = source.read_text(encoding='utf-8').replace('/var/log/fsn-stats-proxy', str(logs)).replace('fsn-stats-proxy.service', units['proxy']).replace('fsn-stats-proxy fsn-stats-proxy', 'rehearsal rehearsal')
    write(private / 'logrotate.conf', rotation, 0o600)
    write(output / 'logrotate.conf', rotation)
    run('verify-units', ['systemd-analyze', 'verify', *[Path('/run/systemd/system') / unit for unit in units.values()]])
    control('daemon-reload')
    control('start', units['proxy'])
    wait(lambda: request()['status'] == 200, 'HTTPS ready')
    initial = status(units['proxy'])
    pid = int(initial['MainPID'])
    assert request()['body'] == (dashboard / 'react-frontend/build/index.html').read_bytes()
    assert request()['serial'] == '01'
    process_status = (Path('/proc') / str(pid) / 'status').read_text()
    assert '\nUid:\t1000\t1000\t1000\t1000\n' in process_status
    assert request('/primus')['status'] == 404
    write(backend_dir / 'reporter.json', json.dumps({'port': port, 'secret': secret, 'ca': str(private / 'ca.crt')}), 0o600, 1000, 1000)
    reporter_log = (output / 'reporter.log').open('wb')
    files.append(reporter_log)
    reporter = subprocess.Popen(['runuser', '-u', 'rehearsal', '--', str(node), str(bundle / 'reporter.cjs'), str(dashboard), str(backend_dir / 'reporter.json')], stdout=reporter_log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(reporter)
    wait(fresh, 'initial telemetry')
    checkpoint('supervised-https-wss', {'state': initial, 'uid': 1000, 'certificate_serial': '01', 'height': 901})
    workers = children(pid)
    assert len(workers) == 1
    before_connections = connects()
    for name in ['nginx-access.log', 'nginx-error.log']:
        with (logs / name).open('ab') as log:
            log.write(b'rotation-fixture-padding\n' * 350000)
    before_inodes = {name: (logs / name).stat().st_ino for name in ['nginx-access.log', 'nginx-error.log']}
    timer_override = Path('/run/systemd/system') / (units['timer'] + '.d') / '50-test.conf'
    timer_override.parent.mkdir()
    write(timer_override, '[Timer]\nOnCalendar=\nOnActiveSec=1s\nAccuracySec=1ms\nPersistent=no\n')
    write(output / 'timer-test-override.conf', timer_override.read_text())
    installed.append(timer_override)
    control('daemon-reload')
    control('start', units['timer'])
    wait(lambda: (logs / 'nginx-access.log.1').exists() and status(units['rotate'])['ActiveState'] == 'inactive', 'timer rotation')
    rotation_state = status(units['rotate'])
    assert rotation_state['Result'] == 'success' and rotation_state['ExecMainStatus'] == '0'
    current_fds = wait(lambda: reopened([pid, *workers]), 'reopened logs')
    assert all((logs / name).stat().st_ino != inode for name, inode in before_inodes.items())
    control('stop', units['timer'])
    checkpoint('timer-rotation-reopen', {'rotation': rotation_state, 'descriptors': current_fds, 'master_unchanged': status(units['proxy'])['MainPID'] == str(pid)})
    for index in range(1, 9):
        assert request('/rotation-' + str(index))['status'] == 404
        assert request('/stats-api/nodes?fault=rotation-' + str(index))['status'] == 502
        run('force-rotation-' + str(index), ['/usr/sbin/logrotate', '--force', '--state', state / 'status', private / 'logrotate.conf'])
        wait(lambda: reopened([pid, *workers]), 'forced reopen')
    retained = {}
    for name in ['nginx-access.log', 'nginx-error.log']:
        paths = sorted(logs.glob(name + '*'))
        expected_names = sorted([name, name + '.1', *[name + '.' + str(index) + '.gz' for index in range(2, 8)]])
        assert [path.name for path in paths] == expected_names
        for index in range(1, 8):
            path = logs / (name + '.' + str(index) + ('.gz' if index > 1 else ''))
            content = gzip.decompress(path.read_bytes()) if index > 1 else path.read_bytes()
            assert ('rotation-' + str(9 - index)).encode() in content
            assert b'rotation-fixture-padding' not in content and b'rotation-1 ' not in content
        assert (logs / name).stat().st_uid == 1000 and (logs / name).stat().st_mode & 0o777 == 0o640
        retained[name] = [path.name for path in paths]
    assert connects() == before_connections
    assert status(units['proxy'])['MainPID'] == str(pid)
    wait(fresh, 'telemetry after rotations')
    checkpoint('archive-retention', {'files': retained, 'telemetry_connection_unchanged': True})
    before_connections = connects()
    select_certificate('certificate-2')
    reloaded_at = time.monotonic()
    control('reload', units['proxy'])
    wait(lambda: request().get('serial') == '02', 'replacement certificate')
    wait(lambda: connects() > before_connections and not any(Path('/proc', str(worker)).exists() for worker in workers), 'old workers retired', timeout=15)
    wait(fresh, 'reporter after certificate reload')
    assert status(units['proxy'])['MainPID'] == str(pid)
    checkpoint('certificate-reload', {'serial': '02', 'master_unchanged': True, 'old_workers_retired_seconds': time.monotonic() - reloaded_at, 'reporter_reconnected': True})
    bad = private / 'certificate-invalid'
    bad.mkdir(mode=0o750)
    os.chown(bad, 0, 1000)
    shutil.copyfile(private / 'certificate-2/cert.pem', bad / 'cert.pem')
    shutil.copyfile(private / 'certificate-1/key.pem', bad / 'key.pem')
    (bad / 'key.pem').chmod(0o640)
    os.chown(bad / 'key.pem', 0, 1000)
    workers = children(pid)
    select_certificate('certificate-invalid')
    rejected = control('reload', units['proxy'], expected=None)
    assert rejected.returncode != 0
    assert request()['serial'] == '02' and request()['status'] == 200
    assert children(pid) == workers and status(units['proxy'])['MainPID'] == str(pid)
    select_certificate('certificate-2')
    checkpoint('invalid-certificate-refusal', {'reload_failed': True, 'serving_serial': '02', 'workers_unchanged': True, 'valid_selection_restored': True})
    before_connections = connects()
    os.kill(workers[0], signal.SIGKILL)
    wait(lambda: children(pid) and workers[0] not in children(pid), 'worker replacement')
    wait(lambda: connects() > before_connections, 'worker crash WSS recovery')
    wait(fresh, 'worker crash report recovery')
    assert status(units['proxy'])['MainPID'] == str(pid)
    checkpoint('worker-crash', {'master_unchanged': True, 'new_workers': children(pid), 'reporter_reconnected': True})
    before = status(units['proxy'])
    old_workers = children(pid)
    before_connections = connects()
    control('kill', '--kill-whom=main', '--signal=SIGKILL', units['proxy'])
    after = wait(lambda: status(units['proxy']) if status(units['proxy'])['MainPID'] not in ['0', str(pid)] else False, 'proxy master restart')
    wait(lambda: connects() > before_connections and fresh(), 'master crash WSS recovery')
    assert not any(Path('/proc', str(worker)).exists() for worker in old_workers)
    assert int(after['NRestarts']) == int(before['NRestarts']) + 1
    assert int((runtime / 'nginx.pid').read_text()) == int(after['MainPID'])
    checkpoint('master-crash', {'before': before, 'after': after, 'old_workers_gone': True, 'reporter_reconnected': True})
    reporter.terminate()
    reporter.wait(timeout=8)
    stop_at = time.monotonic()
    control('stop', units['proxy'])
    stop_seconds = time.monotonic() - stop_at
    time.sleep(6)
    stopped = status(units['proxy'])
    assert stopped['MainPID'] == '0' and stopped['ActiveState'] == 'inactive' and stopped['Result'] == 'success'
    assert stop_seconds < 15
    run('stopped-rotation', ['/usr/sbin/logrotate', '--force', '--state', state / 'status', private / 'logrotate.conf'])
    checkpoint('intentional-stop', {'state': stopped, 'seconds': stop_seconds, 'rotation_while_stopped_passed': True})
    record['passed'] = True
except BaseException:
    record['failure'] = traceback.format_exc()
    print(record['failure'], flush=True)
finally:
    control('stop', units['timer'], units['rotate'], units['proxy'], expected=None)
    record['final_proxy'] = status(units['proxy'])
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=8)
    for file in files:
        file.close()
    run('journal', ['journalctl', '--namespace=' + prefix, '--no-pager', '-o', 'short-iso'], expected=None)
    run('manager-journal', ['journalctl', '--no-pager', '-o', 'short-iso', *sum([['-u', unit] for unit in units.values()], [])], expected=None)
    if logs.exists():
        for path in logs.iterdir():
            if path.is_file() and path.stat().st_size < 131072:
                shutil.copyfile(path, output / path.name)
    control('stop', 'systemd-journald@' + prefix + '.service', 'systemd-journald@' + prefix + '.socket', 'systemd-journald-varlink@' + prefix + '.socket', expected=None)
    control('reset-failed', *units.values(), expected=None)
    for path in installed:
        path.unlink(missing_ok=True)
        if path.parent.name.endswith(('.conf.d', '.timer.d')):
            path.parent.rmdir()
    control('daemon-reload', expected=None)
    process_list = subprocess.check_output(['ps', '-eo', 'pid=,args=']).decode().splitlines()
    lingering = [line for line in process_list if str(private) in line or str(runtime) + '/' in line]
    assert lingering == [], lingering
    removed = []
    for path, parent in [(private, Path('/run')), (runtime, Path('/run')), (logs, Path('/var/log')), (state, Path('/var/lib'))]:
        assert path.name.startswith(prefix) and not path.is_symlink() and path.resolve().parent == parent
        if path.exists():
            shutil.rmtree(path)
        removed.append(str(path))
    machine = Path('/etc/machine-id').read_text().strip()
    for parent in [Path('/run/log/journal'), Path('/var/log/journal')]:
        path = parent / (machine + '.' + prefix)
        assert not path.is_symlink() and path.resolve().parent == parent.resolve()
        if path.exists():
            shutil.rmtree(path)
        removed.append(str(path))
    for path in output.iterdir():
        if path.is_file():
            assert secret.encode() not in path.read_bytes(), 'Synthetic secret appeared in ' + path.name
    record['cleanup'] = {'remaining_processes': lingering, 'runtime_units_removed': all(not path.exists() for path in installed), 'removed_paths': removed, 'all_paths_removed': all(not Path(path).exists() for path in removed), 'no_synthetic_secret_in_evidence': True}
    record['runtime_sha256'] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [node, nginx]}
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': record['passed'], 'cleanup': record['cleanup']}), flush=True)
sys.exit(0 if record['passed'] else 1)
