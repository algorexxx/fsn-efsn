import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
import traceback
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
assert os.geteuid() == 0 and re.fullmatch(r'journal-[1-9][0-9]*', sys.argv[1])
output = bundle / sys.argv[1]
output.mkdir(exist_ok=False)
namespace = 'fsn-stats-log-test-' + secrets.token_hex(4)
unit = namespace + '.service'
unit_path = Path('/run/systemd/system') / unit
config_path = Path('/run/systemd') / ('journald@' + namespace + '.conf.d') / '50-test.conf'
record = {'passed': False, 'namespace': namespace, 'commands': []}


def run(name, args, expected=0):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    (output / (name + '.stdout.txt')).write_bytes(result.stdout)
    (output / (name + '.stderr.txt')).write_bytes(result.stderr)
    record['commands'].append({'name': name, 'exit': result.returncode})
    if expected is not None:
        assert result.returncode == expected, name
    return result


try:
    source = dashboard / 'deploy/systemd/journald@fsn-stats.conf'
    record['candidate_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    config = source.read_text(encoding='utf-8').replace('Storage=persistent', 'Storage=volatile').replace('RateLimitIntervalSec=30s', 'RateLimitIntervalSec=0') + 'Compress=no\n'
    config_path.parent.mkdir()
    config_path.write_text(config, encoding='utf-8')
    (output / 'journal.conf').write_text(config, encoding='utf-8')
    service = f'[Unit]\nDescription=Temporary bounded journal rotation probe\n[Service]\nType=oneshot\nRemainAfterExit=yes\nDynamicUser=yes\nExecStart=/usr/bin/python3 {bundle / "log-probe.py"}\nLogNamespace={namespace}\nLogRateLimitIntervalSec=0\nStandardOutput=journal\nStandardError=journal\nNoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nLimitCORE=0\n'
    unit_path.write_text(service, encoding='utf-8')
    (output / unit).write_text(service, encoding='utf-8')
    run('reload', ['systemctl', 'daemon-reload'])
    run('start', ['systemctl', 'start', unit])
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        last = subprocess.run(['journalctl', '--namespace=' + namespace, '--no-pager', '-g', '^supervision-log-last-marker$'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        if last.returncode == 0:
            break
        time.sleep(0.1)
    assert last.returncode == 0, 'Last log marker did not arrive'
    run('sync', ['journalctl', '--namespace=' + namespace, '--sync'])
    first = run('first-marker', ['journalctl', '--namespace=' + namespace, '--no-pager', '-g', '^supervision-log-first-marker$'], expected=1)
    run('last-marker', ['journalctl', '--namespace=' + namespace, '--no-pager', '-g', '^supervision-log-last-marker$'])
    run('disk-usage', ['journalctl', '--namespace=' + namespace, '--disk-usage'])
    directory = Path('/run/log/journal') / (Path('/etc/machine-id').read_text().strip() + '.' + namespace)
    files = {path.name: path.stat().st_blocks * 512 for path in directory.glob('*.journal*')}
    total = sum(files.values())
    assert 0 < total <= 24 * 1024 * 1024
    record.update(passed=True, allocated_bytes=total, files=files, first_marker_evicted=True, last_marker_retained=True, runtime_budget_bytes=16777216, asserted_ceiling_bytes=25165824)
except BaseException:
    record['failure'] = traceback.format_exc()
    print(record['failure'], flush=True)
finally:
    run('stop-probe', ['systemctl', 'stop', unit], expected=None)
    run('journal-notices', ['journalctl', '--namespace=' + namespace, '--no-pager', '-p', 'warning', '-n', '30'], expected=None)
    run('stop-journal', ['systemctl', 'stop', 'systemd-journald@' + namespace + '.service', 'systemd-journald@' + namespace + '.socket', 'systemd-journald-varlink@' + namespace + '.socket'], expected=None)
    unit_path.unlink(missing_ok=True)
    config_path.unlink(missing_ok=True)
    config_path.parent.rmdir()
    run('reload-final', ['systemctl', 'daemon-reload'])
    record['runtime_files_removed'] = not unit_path.exists() and not config_path.exists()
    for name in ['run-journal.py', 'log-probe.py']:
        (output / name).write_bytes((bundle / name).read_bytes())
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
sys.exit(0 if record['passed'] else 1)
