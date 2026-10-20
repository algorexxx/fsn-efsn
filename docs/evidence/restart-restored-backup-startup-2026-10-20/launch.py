from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
SOURCE = Path('/home/rehearsal/data/efsn/chaindata')
DEST = Path('/mnt/w/FusionRestart/restored-backup-2026-10-19')
IMAGE = DEST / 'startup.ext4'
BEGIN = time.monotonic()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(name, record):
    with (HERE / name).open('x', encoding='utf-8') as file:
        file.write(json.dumps(record, indent=2) + '\n')

def command(name, args, seconds=600):
    record = {'started': now(), 'argv': ['timeout', '--kill-after=20s', str(seconds) + 's'] + args}
    with (HERE / (name + '.stdout.txt')).open('xb') as output, (HERE / (name + '.stderr.txt')).open('xb') as error:
        result = subprocess.run(record['argv'], stdout=output, stderr=error)
    record.update(finished=now(), exit=result.returncode)
    save(name + '.json', record)
    if result.returncode:
        raise RuntimeError(name + ' failed')
    return (HERE / (name + '.stdout.txt')).read_text(encoding='utf-8')

def inputs():
    for line in (HERE / 'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name

def capacity():
    result = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/w']}
    for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 101)]:
        assert result[path] > gib * 1024**3, (path, result[path])
    return result

def attach(label, read_only=False):
    args = ['losetup', '--find', '--show'] + (['--read-only'] if read_only else []) + [str(IMAGE)]
    device = command(label, args).strip()
    assert re.fullmatch(r'/dev/loop[0-9]+', device)
    identity = json.loads(command(label + '-identity', ['losetup', '--json', '--output', 'NAME,BACK-FILE,RO', device]))
    assert identity['loopdevices'] == [{'name': device, 'back-file': str(IMAGE), 'ro': read_only}]
    return device

def interrupted(signum, frame):
    raise TimeoutError('finite job interrupted by signal ' + str(signum))


def protected():
    from worker import copy, digest
    records = {}
    for path in [SOURCE, Path('/home/rehearsal/replay/candidate-ticket-encoding-working'),
                 Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2')]:
        rows = copy.files(path)
        records[str(path)] = {'files': len(rows), 'metadata_sha256':
                              hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()}
    final_image = Path('/mnt/w/FusionRestart/replay-work-7170976-2026-10-12/replay.ext4')
    stat = final_image.stat()
    records[str(final_image)] = {'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
    return records


def phase(name, source_view, target, image_view, seconds):
    command(name, ['runuser', '-u', 'rehearsal', '--', 'python3', '-B', str(HERE / 'worker.py'),
                   name, str(source_view), str(target), str(image_view)], seconds)


def qualify():
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    links = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(links) == 1 and links[0]['ifname'] == 'lo' and 'UP' not in links[0]['flags']
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS',
                                               '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert mount['target'] == '/mnt/w' and mount['source'] == 'W:' and mount['fstype'] == '9p'
    assert IMAGE.resolve() == IMAGE and IMAGE.is_file() and IMAGE.stat().st_size == 256 * 1024**3
    assert SOURCE.resolve() == SOURCE and SOURCE.is_dir()
    locks = [open(str(SOURCE) + '.run.lock', 'a'), open('/home/rehearsal/replay/w-image-migration.run.lock', 'a')]
    for lock in locks:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    database_lock = (SOURCE / 'LOCK').open('rb')
    fcntl.flock(database_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
    assert not json.loads(subprocess.check_output(['losetup', '--list', '--json'], text=True))['loopdevices']
    processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
    assert not re.search(r'^\s*\d+\s+(?:efsn|replay-tests|observer|storage-probe)\s*$', processes, re.M)
    initial = capacity()
    assert initial['/home/rehearsal'] > 21 * 1024**3 and initial['/mnt/d'] > 51 * 1024**3
    inputs()
    from worker import identities
    identity = identities()
    preserved = protected()
    save('environment.json', {'started': now(), 'mount': mount, 'interfaces': links,
                              'netns': os.readlink('/proc/self/ns/net'), 'parent_netns': sys.argv[2],
                              'free_before': initial, 'image': str(IMAGE), 'identities': identity,
                              'protected_before': preserved, 'processes': processes})
    source_view = Path(tempfile.mkdtemp(prefix='startup-source-'))
    image_view = Path(tempfile.mkdtemp(prefix='startup-image-'))
    source_mounted, image_mounted, target_mounted, device = False, False, False, None
    target = image_view / 'runtime/efsn/chaindata'
    try:
        command('source-bind', ['mount', '--bind', str(SOURCE), str(source_view)])
        source_mounted = True
        command('source-readonly', ['mount', '-o', 'remount,bind,ro', str(source_view)])
        device = attach('attach-initial-readonly', True)
        uuid = command('uuid-initial', ['blkid', '-s', 'UUID', '-o', 'value', device]).strip()
        assert uuid == '0b18a87d-e8ee-413f-b37f-01eec39b0c48'
        command('mount-initial-readonly', ['mount', '-t', 'ext4', '-o', 'ro,noload', device, str(image_view)])
        image_mounted = True
        assert not (image_view / 'runtime').exists()
        phase('prehash', source_view, image_view / 'checkpoint', image_view, 12720)
        command('unmount-initial', ['umount', str(image_view)])
        image_mounted = False
        command('detach-initial', ['losetup', '--detach', device])
        device = None
        device = attach('attach-writable')
        assert command('uuid-writable', ['blkid', '-s', 'UUID', '-o', 'value', device]).strip() == uuid
        command('filesystem-before-write', ['e2fsck', '-f', '-n', device], 1200)
        command('mount-write', ['mount', '-t', 'ext4', device, str(image_view)])
        image_mounted = True
        target.mkdir(mode=0o700, parents=True)
        for directory in [image_view / 'runtime', target.parent, target]:
            os.chown(directory, 1000, 1000)
        command('datadir-bind', ['mount', '--bind', str(image_view / 'checkpoint'), str(target)])
        target_mounted = True
        phase('cli', source_view, image_view / 'runtime', image_view, 1500)
        command('datadir-unmount', ['umount', str(target)])
        target_mounted = False
        command('unmount-write', ['umount', str(image_view)])
        image_mounted = False
        command('filesystem-after-write', ['e2fsck', '-f', '-n', device], 1200)
        command('detach-write', ['losetup', '--detach', device])
        device = None
        device = attach('reattach-cold', True)
        assert command('uuid-cold', ['blkid', '-s', 'UUID', '-o', 'value', device]).strip() == uuid
        command('mount-cold', ['mount', '-t', 'ext4', '-o', 'ro,noload', device, str(image_view)])
        image_mounted = True
        phase('cold', source_view, image_view / 'checkpoint', image_view, 12720)
        assert protected() == preserved and identities() == identity
        inputs()
        save('acceptance.json', {'pass': True, 'finished': now(), 'protected_unchanged': preserved,
                                 'elapsed_seconds': time.monotonic() - BEGIN, 'uuid': uuid,
                                 'original_backup_retained': True, 'selected_release_changed': False})
    finally:
        if target_mounted:
            command('cleanup-datadir-unmount', ['umount', str(target)])
        if image_mounted:
            command('cleanup-image-unmount', ['umount', str(image_view)])
        if device:
            command('cleanup-image-detach', ['losetup', '--detach', device])
        if source_mounted:
            command('cleanup-source-unmount', ['umount', str(source_view)])
        source_view.rmdir()
        image_view.rmdir()
        save('cleanup.json', {'finished': now(), 'mounts_removed': True, 'loop_detached': True,
                              'protected_metadata_unchanged': protected() == preserved,
                              'free_bytes': capacity()})


if __name__ == '__main__':
    assert os.getuid() == 0
    if len(sys.argv) == 1:
        inputs()
        assert not (HERE / 'completion.json').exists() and not (HERE / 'environment.json').exists()
        assert json.loads((HERE / 'controls.json').read_text(encoding='utf-8'))['pass']
        os.execvp('unshare', ['unshare', '--mount', '--', 'python3', '-B', str(__file__), 'mount', os.readlink('/proc/self/ns/mnt')])
    elif sys.argv[1] == 'mount':
        assert os.readlink('/proc/self/ns/mnt') != sys.argv[2]
        subprocess.run(['mount', '--make-rprivate', '/'], check=True)
        old = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET', '-T', '/mnt/w'], text=True))['filesystems'][0]
        assert old['target'] == '/'
        subprocess.run(['mount', '-t', 'drvfs', 'W:', '/mnt/w', '-o', 'uid=1000,gid=1000'], check=True)
        try:
            result = subprocess.run(['unshare', '--net', '--', 'python3', '-B', str(__file__), 'qualify', os.readlink('/proc/self/ns/net')])
        finally:
            subprocess.run(['umount', '/mnt/w'], check=True)
        save('completion.json', {'finished': now(), 'exit': result.returncode, 'verified_pass': result.returncode == 0,
                                 'automatic_replay': False})
        sys.exit(result.returncode)
    elif sys.argv[1] == 'qualify':
        signal.signal(signal.SIGTERM, interrupted)
        qualify()
    else:
        raise RuntimeError('unknown mode')
