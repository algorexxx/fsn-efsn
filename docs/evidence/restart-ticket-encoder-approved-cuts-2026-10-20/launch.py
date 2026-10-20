"""Use the existing private-namespace/read-only-source/one-owner pattern."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path('/home/rehearsal/results/restart-ticket-encoder-regressions-2026-10-08/candidate-recovery')
VIEW = REPO / 'tmp/restart-ticket-encoder-approved-cuts-2026-10-20-source-ro'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, indent=2) + '\n')


def command(name, args):
    record = {'argv': args, 'started': now()}
    with (HERE / (name + '.stdout.txt')).open('xb') as output, (HERE / (name + '.stderr.txt')).open('xb') as errors:
        code = subprocess.call(args, stdout=output, stderr=errors)
    record.update(finished=now(), exit=code)
    save(name + '.json', record)
    assert code == 0, name


def protected():
    result = {}
    for path in [Path('/home/rehearsal/data/efsn/chaindata'),
                 Path('/home/rehearsal/replay/candidate-ticket-encoding-working'),
                 Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2')]:
        rows = {p.name: [p.stat().st_size, p.stat().st_mtime_ns] for p in sorted(path.iterdir()) if p.is_file()}
        result[str(path)] = {'files': len(rows), 'metadata_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()}
    return result


def run():
    assert os.geteuid() == 0
    if len(sys.argv) == 1:
        save('dispatch-claim.json', {'started': now(), 'pid': os.getpid(), 'automatic_retry': False})
        args = ['unshare', '--mount', '--net', '--propagation', 'private', '--',
                'python3', '-B', str(Path(__file__).resolve()), '--isolated', os.readlink('/proc/self/ns/net')]
        code = subprocess.call(args)
        save('completion.json', {'finished': now(), 'exit': code,
                                'verified_pass': code == 0, 'automatic_replay': False})
        return code
    assert len(sys.argv) == 3 and sys.argv[1] == '--isolated'
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    links = json.loads(subprocess.check_output(['ip', '-j', 'link'], text=True))
    assert len(links) == 1 and links[0]['ifname'] == 'lo' and 'UP' not in links[0]['flags']
    owner = open('/home/rehearsal/replay/w-image-migration.run.lock', 'a')
    fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
    loops = json.loads(subprocess.check_output(['losetup', '--json'], text=True))['loopdevices']
    for loop in loops:
        assert loop['ro'] and loop['autoclear'] and '.iso/' in loop['back-file']
        assert loop['back-file'].startswith('/mnt/docker-desktop-disk/isocache/entries/')
    processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
    assert not re.search(r'^\s*\d+\s+(?:efsn|fsn-recovery|operator-tests|approval-tests|replay-tests|observer|storage-probe|go)\s*$', processes, re.M)
    for line in (HERE / 'INPUT_SHA256SUMS').read_text().splitlines():
        digest, name = line.split(None, 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
    assert not VIEW.exists()
    before = protected()
    save('environment.json', {'started': now(), 'netns': os.readlink('/proc/self/ns/net'),
         'parent_netns': sys.argv[2], 'interfaces': links, 'processes': processes,
         'unrelated_readonly_docker_iso_loops': loops, 'protected_before': before,
         'no_test_image_attached': True, 'data_and_build_root': str(REPO / 'tmp' / HERE.name)})
    VIEW.mkdir()
    mounted = False
    try:
        command('source-bind', ['mount', '--bind', str(SOURCE), str(VIEW)])
        mounted = True
        command('source-readonly', ['mount', '-o', 'remount,bind,ro', str(VIEW)])
        command('worker', ['timeout', '--kill-after=20s', '2220s', 'runuser', '-u', 'rehearsal',
                          '--', 'python3', '-B', str(HERE / 'run.py'), str(VIEW), sys.argv[2]])
        result = json.loads((HERE / 'qualification/run.json').read_text())
        assert result['completed'] and result['preservation_pass']
        assert protected() == before
        save('acceptance.json', {'pass': True, 'finished': now(), 'protected_unchanged': before,
                                'selected_release_changed': False, 'real_keys_used': False})
    finally:
        if mounted:
            command('source-unmount', ['umount', str(VIEW)])
        # Empty mountpoint is retained; no destructive cleanup is needed.
        save('cleanup.json', {'finished': now(), 'source_unmounted': not os.path.ismount(VIEW),
                             'protected_metadata_unchanged': protected() == before,
                             'test_image_attached': False})
    return 0


def interrupted(signum, frame):
    raise TimeoutError('launcher interrupted by signal ' + str(signum))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    sys.exit(run())
