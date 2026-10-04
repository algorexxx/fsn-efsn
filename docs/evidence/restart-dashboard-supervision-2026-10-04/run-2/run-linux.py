import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
assert os.geteuid() == 0
assert re.fullmatch(r'run-[1-9][0-9]*', sys.argv[1])
output = bundle / sys.argv[1]
output.mkdir(exist_ok=False)
for source in ['run-linux.py', 'reporter.cjs', 'log-probe.py']:
    shutil.copyfile(bundle / source, output / source)
private = Path(tempfile.mkdtemp(prefix='fusion-dashboard-supervision-', dir='/home/rehearsal'))
os.chown(private, 1000, 1000)
namespace = 'fsn-stats-test-' + secrets.token_hex(4)
units = {role: namespace + '-' + role + '.service' for role in ['collector', 'writer', 'api']}
probe_unit = namespace + '-log.service'
node = root / 'tmp/dashboard-runtime-review/v24.21.0/node'
pg_root = root / 'tmp/dashboard-postgres-linux-runtime/extracted'
pg_bin = pg_root / 'usr/lib/postgresql/16/bin'
pg_env = ['env', 'LD_LIBRARY_PATH=' + str(pg_root / 'usr/lib/x86_64-linux-gnu'), 'PGPASSFILE=' + str(private / 'pgpass')]
passwords = {role: secrets.token_hex(24) for role in ['admin', 'writer', 'api']}
telemetry_secret = secrets.token_hex(24)
processes = []
installed = []
started_database = False
record = {'passed': False, 'commands': [], 'checkpoints': [], 'private': str(private), 'namespace': namespace, 'units': units}


def write(path, value, protected=False):
    path.write_text(value, encoding='utf-8', newline='\n')
    if protected:
        path.chmod(0o600)
        os.chown(path, 1000, 1000)


def run(name, command, timeout=35, expected=0, save=True):
    result = subprocess.run([str(value) for value in command], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if save:
        (output / (name + '.stdout.txt')).write_bytes(result.stdout)
        (output / (name + '.stderr.txt')).write_bytes(result.stderr)
        record['commands'].append({'name': name, 'exit': result.returncode})
    if expected is not None:
        assert result.returncode == expected, (name, result.returncode, result.stderr.decode(errors='replace'))
    return result


def systemctl(*args, save=False, expected=0):
    return run('systemctl-' + str(len(record['commands'])), ['systemctl', *args], expected=expected, save=save)


def status(role):
    values = systemctl('show', units[role], '-p', 'MainPID', '-p', 'NRestarts', '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result', '-p', 'ExecMainStatus', '-p', 'ControlGroup').stdout.decode()
    return dict(line.split('=', 1) for line in values.splitlines())


def wait(check, label, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError('Deadline: ' + label)


def checkpoint(label, value):
    record['checkpoints'].append({'name': label, **value})
    print(label, json.dumps(value), flush=True)


def port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def pg_command(binary, *args):
    return ['runuser', '-u', 'rehearsal', '--', *pg_env, pg_bin / binary, *args]


def sql(query):
    return run('sql', pg_command('psql', '-h', '127.0.0.1', '-p', str(pg_port), '-U', 'dashboard_test_admin', '-d', 'postgres', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-c', query), save=False).stdout.decode().strip()


def http():
    try:
        with urllib.request.urlopen('http://127.0.0.1:' + str(api_port) + '/nodes', timeout=6) as response:
            return {'status': response.status, 'body': json.load(response), 'observed': response.headers.get('X-Dashboard-Observed-At')}
    except urllib.error.HTTPError as error:
        return {'status': error.code, 'body': json.load(error)}
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return {'status': 0}


def fresh(height):
    response = http()
    if response['status'] == 200 and len(response['body']) == 1 and response['body'][0]['block'] == height:
        return response
    return False


def set_height(height):
    temporary = private / 'control.new'
    write(temporary, json.dumps({'port': collector_port, 'secret': telemetry_secret, 'height': height}), True)
    temporary.replace(private / 'control.json')


def start_database(label):
    return run(label, pg_command('pg_ctl', '-D', private / 'data', '-l', private / 'postgres.log', '-o', f'-h 127.0.0.1 -p {pg_port} -k {private} -c shared_buffers=16MB -c max_connections=20 -c jit=off', '-w', 'start'))


collector_port, api_port, pg_port = port(), port(), port()
assert len({collector_port, api_port, pg_port}) == 3
record['ports'] = {'collector': collector_port, 'api': api_port, 'postgres': pg_port}
try:
    run('systemd-version', ['systemctl', '--version'])
    run('node-version', [node, '--version'])
    run('postgres-version', pg_command('postgres', '--version'))
    for role, password in passwords.items():
        write(private / (role + '.password'), password, True)
    write(private / 'telemetry.json', json.dumps({'supervision-node': telemetry_secret}), True)
    write(private / 'pgpass', f'127.0.0.1:{pg_port}:postgres:dashboard_test_admin:{passwords["admin"]}\n', True)
    run('initdb', pg_command('initdb', '-D', private / 'data', '-L', pg_root / 'usr/share/postgresql/16', '-U', 'dashboard_test_admin', '-A', 'scram-sha-256', '--pwfile', private / 'admin.password', '--encoding=UTF8', '--locale=C'))
    start_database('database-start')
    started_database = True
    provisioning = (dashboard / 'db/schema/001-dashboard.sql').read_text(encoding='utf-8')
    provisioning += f"\nCREATE ROLE supervision_writer LOGIN PASSWORD '{passwords['writer']}';\nCREATE ROLE supervision_api LOGIN PASSWORD '{passwords['api']}';\n"
    provisioning += 'GRANT USAGE ON SCHEMA dashboard_v1 TO supervision_writer, supervision_api;\nGRANT SELECT, INSERT, UPDATE ON dashboard_v1.snapshot TO supervision_writer;\nGRANT SELECT ON dashboard_v1.snapshot TO supervision_api;\n'
    write(private / 'provision.sql', provisioning, True)
    run('provision', pg_command('psql', '-h', '127.0.0.1', '-p', str(pg_port), '-U', 'dashboard_test_admin', '-d', 'postgres', '-X', '-v', 'ON_ERROR_STOP=1', '-f', private / 'provision.sql'))
    environments = {
        'collector': {'GEOIP_MODE': 'disabled', 'COLLECTOR_HOST': '127.0.0.1', 'COLLECTOR_PORT': collector_port, 'COLLECTOR_MAX_MESSAGE_BYTES': 4194304, 'COLLECTOR_MAX_HEAD_BYTES': 65536, 'COLLECTOR_MAX_NODES': 8, 'COLLECTOR_MAX_CONNECTIONS': 16, 'COLLECTOR_HELLO_TIMEOUT_MS': 1000, 'COLLECTOR_MESSAGES_PER_SECOND': 100, 'COLLECTOR_MAX_BUFFERED_BYTES': 1048576, 'VERBOSITY': 2},
        'writer': {'COLLECTOR_WS_URL': f'ws://127.0.0.1:{collector_port}/primus', 'SNAPSHOT_INTERVAL_MS': 1000, 'SNAPSHOT_TIMEOUT_MS': 6000, 'SNAPSHOT_MAX_BYTES': 1048576, 'SNAPSHOT_MAX_NODES': 8},
        'api': {'API_HOST': '127.0.0.1', 'API_PORT': api_port, 'SNAPSHOT_MAX_AGE_MS': 10000, 'NODE_REPORT_MAX_AGE_MS': 10000},
    }
    for role in ['writer', 'api']:
        environments[role].update(DB_HOST='127.0.0.1', DB_PORT=pg_port, DB_NAME='postgres', DB_USER='supervision_' + role, DB_TIMEOUT_MS=5000)
    for role, values in environments.items():
        write(private / (role + '.env'), ''.join(f'{key}={value}\n' for key, value in values.items()), True)
        shutil.copyfile(private / (role + '.env'), output / (role + '.env'))
        unit = (dashboard / 'deploy/systemd' / ('fsn-stats-' + role + '.service')).read_text(encoding='utf-8')
        unit = unit.replace('/opt/fsn-stats/current', str(dashboard)).replace('/opt/fsn-stats/node/bin/node', str(node)).replace('/etc/fsn-stats/credentials', str(private)).replace('/etc/fsn-stats', str(private)).replace('LogNamespace=fsn-stats', 'LogNamespace=' + namespace)
        write(output / units[role], unit)
        destination = Path('/run/systemd/system') / units[role]
        assert not destination.exists()
        write(destination, unit)
        installed.append(destination)
    journal = (dashboard / 'deploy/systemd/journald@fsn-stats.conf').read_text(encoding='utf-8').replace('Storage=persistent', 'Storage=volatile')
    journal += 'Compress=no\n'
    journal_path = Path('/run/systemd') / ('journald@' + namespace + '.conf.d') / '50-test.conf'
    assert not journal_path.exists()
    journal_path.parent.mkdir()
    write(journal_path, journal)
    installed.append(journal_path)
    write(output / 'journal.conf', journal)
    run('unit-verify', ['systemd-analyze', 'verify', *[str(Path('/run/systemd/system') / unit) for unit in units.values()]])
    systemctl('daemon-reload', save=True)
    systemctl('start', units['writer'], units['api'], save=True)
    wait(lambda: http().get('body') == {'error': 'snapshot_unavailable'}, 'empty API')
    writer_initial = status('writer')['MainPID']
    systemctl('start', units['collector'], save=True)
    set_height(701)
    reporter_log = (output / 'reporter.log').open('wb')
    reporter = subprocess.Popen(['runuser', '-u', 'rehearsal', '--', str(node), str(bundle / 'reporter.cjs'), str(dashboard), str(private / 'control.json')], stdout=reporter_log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(reporter)
    response = wait(lambda: fresh(701), 'initial snapshot')
    states = {role: status(role) for role in units}
    identities = {role: Path('/proc/' + value['MainPID'] + '/status').read_text().split('Uid:')[1].splitlines()[0].strip() for role, value in states.items()}
    assert writer_initial == states['writer']['MainPID']
    assert all(int(value.split()[0]) != 0 for value in identities.values())
    assert len(set(identities.values())) == 3
    checkpoint('late-collector-start', {'states': states, 'identities': identities, 'height': response['body'][0]['block']})
    for role, height in [('collector', 702), ('writer', 703), ('api', 704)]:
        expected_other = {name: status(name)['MainPID'] for name in units if name != role}
        before = status(role)
        set_height(height)
        systemctl('kill', '--kill-whom=main', '--signal=SIGKILL', units[role], save=True)
        wait(lambda: status(role)['MainPID'] not in ['0', before['MainPID']], role + ' new PID')
        response = wait(lambda: fresh(height), role + ' recovered snapshot')
        after = status(role)
        actual_other = {name: status(name)['MainPID'] for name in units if name != role}
        assert actual_other == expected_other
        assert int(after['NRestarts']) == int(before['NRestarts']) + 1
        checkpoint(role + '-crash-recovery', {'before': before, 'after': after, 'other_pids_unchanged': True, 'height': response['body'][0]['block']})
    before_database_outage = {name: status(name)['MainPID'] for name in units}
    run('database-stop-outage', pg_command('pg_ctl', '-D', private / 'data', '-m', 'fast', '-w', 'stop'))
    started_database = False
    outage = wait(lambda: http().get('body') == {'error': 'snapshot_unavailable'}, 'database unavailable')
    time.sleep(3)
    start_database('database-restart')
    started_database = True
    set_height(705)
    wait(lambda: fresh(705), 'database reconnect')
    after_database_outage = {name: status(name)['MainPID'] for name in units}
    assert after_database_outage == before_database_outage
    checkpoint('database-recovery', {'same_application_pids': True, 'unavailable_during_outage': outage, 'height': 705})
    previous_observed = sql('SELECT observed_at FROM dashboard_v1.snapshot')
    lock_log = (output / 'database-lock.log').open('wb')
    lock = subprocess.Popen([str(value) for value in pg_command('psql', '-h', '127.0.0.1', '-p', str(pg_port), '-U', 'dashboard_test_admin', '-d', 'postgres', '-X', '-v', 'ON_ERROR_STOP=1', '-c', "BEGIN; LOCK TABLE dashboard_v1.snapshot IN ACCESS EXCLUSIVE MODE; SELECT pg_sleep(4); COMMIT;")], stdout=lock_log, stderr=subprocess.STDOUT)
    processes.append(lock)
    wait(lambda: sql("SELECT count(*) FROM pg_stat_activity WHERE usename='supervision_writer' AND wait_event_type='Lock'") == '1', 'pending writer transaction', timeout=5)
    stop_started = time.monotonic()
    systemctl('stop', units['writer'], save=True)
    drain_seconds = time.monotonic() - stop_started
    lock.wait(timeout=6)
    lock_log.close()
    after_drain = status('writer')
    next_observed = sql('SELECT observed_at FROM dashboard_v1.snapshot')
    assert lock.returncode == 0
    assert after_drain['ActiveState'] == 'inactive' and after_drain['ExecMainStatus'] == '0'
    assert next_observed != previous_observed
    assert drain_seconds < 15
    checkpoint('pending-write-shutdown', {'status': after_drain, 'drain_seconds': drain_seconds, 'new_snapshot_committed': True})
    wait(lambda: http().get('body') == {'error': 'snapshot_unavailable'}, 'stale writer', timeout=15)
    systemctl('start', units['writer'], save=True)
    set_height(706)
    wait(lambda: fresh(706), 'writer explicit restart')
    checkpoint('stale-and-recover', {'height': 706})
    reporter.terminate()
    reporter.wait(timeout=8)
    reporter_log.close()
    systemctl('stop', *units.values(), save=True)
    time.sleep(6)
    stopped_states = {role: status(role) for role in units}
    assert all(item['MainPID'] == '0' and item['ActiveState'] == 'inactive' and item['Result'] == 'success' for item in stopped_states.values())
    checkpoint('intentional-stop', {'states': stopped_states, 'held_seconds': 6})
    collector_environment = (private / 'collector.env').read_text(encoding='utf-8')
    write(private / 'collector.env', collector_environment.replace('GEOIP_MODE=disabled', 'GEOIP_MODE=invalid'), True)
    systemctl('reset-failed', units['collector'])
    systemctl('start', units['collector'], save=True)
    limited = wait(lambda: status('collector') if status('collector')['Result'] == 'start-limit-hit' else False, 'invalid configuration restart limit', timeout=35)
    assert limited['ActiveState'] == 'failed' and limited['MainPID'] == '0'
    assert limited['NRestarts'] == '5'
    checkpoint('restart-limit', {'status': limited})
    write(private / 'collector.env', collector_environment, True)
    systemctl('reset-failed', units['collector'])
    systemctl('start', *units.values(), save=True)
    set_height(707)
    reporter_log = (output / 'reporter-repair.log').open('wb')
    reporter = subprocess.Popen(['runuser', '-u', 'rehearsal', '--', str(node), str(bundle / 'reporter.cjs'), str(dashboard), str(private / 'control.json')], stdout=reporter_log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(reporter)
    wait(lambda: fresh(707), 'configuration repair')
    checkpoint('configuration-repair', {'height': 707})
    reporter.terminate()
    reporter.wait(timeout=8)
    reporter_log.close()
    systemctl('stop', *units.values(), save=True)
    logs = run('application-journal', ['journalctl', '--namespace=' + namespace, '--no-pager', '-o', 'short-iso']).stdout
    assert all(secret.encode() not in logs for secret in [telemetry_secret, *passwords.values()])
    checkpoint('credential-log-check', {'secrets_present': False, 'log_bytes': len(logs)})
    probe = f'[Unit]\nDescription=Temporary bounded journal probe\n[Service]\nType=oneshot\nDynamicUser=yes\nExecStart=/usr/bin/python3 {bundle / "log-probe.py"}\nLogNamespace={namespace}\nLogRateLimitIntervalSec=0\nStandardOutput=journal\nStandardError=journal\nNoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nLimitCORE=0\n'
    probe_path = Path('/run/systemd/system') / probe_unit
    assert not probe_path.exists()
    write(probe_path, probe)
    write(output / probe_unit, probe)
    installed.append(probe_path)
    systemctl('daemon-reload')
    systemctl('start', probe_unit, save=True)
    run('journal-sync', ['journalctl', '--namespace=' + namespace, '--sync'])
    log_directory = Path('/run/log/journal') / (Path('/etc/machine-id').read_text().strip() + '.' + namespace)
    retained = list(log_directory.glob('*.journal*'))
    total = sum(item.stat().st_blocks * 512 for item in retained)
    first = run('first-log-marker', ['journalctl', '--namespace=' + namespace, '--no-pager', '-g', '^supervision-log-first-marker$'], expected=1)
    last = run('last-log-marker', ['journalctl', '--namespace=' + namespace, '--no-pager', '-g', '^supervision-log-last-marker$'])
    assert 0 < total <= 24 * 1024 * 1024
    assert b'supervision-log-last-marker' in last.stdout
    checkpoint('journal-rotation', {'allocated_bytes': total, 'file_count': len(retained), 'first_marker_evicted': first.returncode == 1, 'last_marker_retained': True, 'runtime_budget_bytes': 16777216, 'asserted_ceiling_bytes': 25165824})
    run('journal-disk-usage', ['journalctl', '--namespace=' + namespace, '--disk-usage'])
    record['passed'] = True
except BaseException:
    record['failure'] = traceback.format_exc()
    print(record['failure'], flush=True)
finally:
    cleanup_errors = []
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=8)
    try:
        systemctl('stop', *units.values(), probe_unit, expected=None)
        record['final_states'] = {role: status(role) for role in units}
        run('final-journal-tail', ['journalctl', '--namespace=' + namespace, '--no-pager', '-n', '20'], expected=None)
        run('service-manager-journal', ['journalctl', '--no-pager', '-o', 'short-iso', *sum([['-u', unit] for unit in units.values()], [])], expected=None)
        systemctl('stop', 'systemd-journald@' + namespace + '.service', 'systemd-journald@' + namespace + '.socket', 'systemd-journald-varlink@' + namespace + '.socket', expected=None)
        systemctl('reset-failed', *units.values(), probe_unit, expected=None)
    except BaseException as error:
        cleanup_errors.append(str(error))
    if started_database:
        try:
            run('database-stop-final', pg_command('pg_ctl', '-D', private / 'data', '-m', 'fast', '-w', 'stop'))
        except BaseException as error:
            cleanup_errors.append(str(error))
    if (private / 'postgres.log').exists():
        shutil.copyfile(private / 'postgres.log', output / 'postgres.log')
    for name in ['admin.password', 'writer.password', 'api.password', 'pgpass', 'provision.sql', 'telemetry.json', 'control.json', 'control.new']:
        (private / name).unlink(missing_ok=True)
    for path in installed:
        path.unlink(missing_ok=True)
        if path.parent.name.endswith('.conf.d'):
            path.parent.rmdir()
    systemctl('daemon-reload', expected=None)
    record['cleanup'] = {'errors': cleanup_errors, 'unit_files_removed': all(not path.exists() for path in installed), 'postgres_pid_absent': not (private / 'data/postmaster.pid').exists(), 'fixture_processes_stopped': all(process.poll() is not None for process in processes), 'private_plaintext_removed': all(not (private / name).exists() for name in ['admin.password', 'writer.password', 'api.password', 'pgpass', 'provision.sql', 'telemetry.json', 'control.json', 'control.new'])}
    record['source_sha256'] = {path.relative_to(dashboard).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in (dashboard / 'deploy/systemd').iterdir()}
    record['runner_sha256'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in bundle.iterdir() if path.suffix in ['.py', '.cjs']}
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': record['passed'], 'cleanup': record['cleanup']}), flush=True)
sys.exit(0 if record['passed'] and not cleanup_errors else 1)
