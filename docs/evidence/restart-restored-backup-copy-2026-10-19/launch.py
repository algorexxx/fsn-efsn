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
    for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 356)]:
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

def migrate():
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    links = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(links) == 1 and links[0]['ifname'] == 'lo' and 'UP' not in links[0]['flags']
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert mount['target'] == '/mnt/w' and mount['source'] == 'W:' and mount['fstype'] == '9p'
    assert SOURCE.resolve() == SOURCE and SOURCE.is_dir() and not DEST.exists()
    assert DEST.parent.resolve() == DEST.parent and DEST.parent.is_dir()
    assert not json.loads(subprocess.check_output(['losetup', '--list', '--json'], text=True))['loopdevices'], 'another image is attached'
    locks = [open(str(SOURCE) + '.run.lock', 'a'), open('/home/rehearsal/replay/w-image-migration.run.lock', 'a')]
    for lock in locks:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    database_lock = (SOURCE / 'LOCK').open('rb')
    fcntl.flock(database_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
    processes = subprocess.check_output(['ps', '-eo', 'pid,comm'], text=True)
    assert not re.search(r'^\s*\d+\s+(?:efsn|replay-tests|observer|storage-probe)\s*$', processes, re.M)
    initial = capacity()
    assert initial['/home/rehearsal'] > 21 * 1024**3 and initial['/mnt/d'] > 51 * 1024**3
    save('environment.json', {'started': now(), 'mount': mount, 'interfaces': links,
          'netns': os.readlink('/proc/self/ns/net'), 'parent_netns': sys.argv[2],
          'free_before': capacity(), 'image_virtual_bytes': 256 * 1024**3,
          'source': str(SOURCE), 'image': str(IMAGE), 'processes': processes})
    inputs()
    from worker import expected
    expected()
    source_view = Path(tempfile.mkdtemp(prefix='w-copy-source-'))
    image_view = Path(tempfile.mkdtemp(prefix='w-copy-image-'))
    source_mounted, image_mounted, device = False, False, None
    try:
        command('source-bind', ['mount', '--bind', str(SOURCE), str(source_view)])
        source_mounted = True
        command('source-readonly', ['mount', '-o', 'remount,bind,ro', str(source_view)])
        DEST.mkdir()
        with IMAGE.open('xb') as file:
            file.truncate(256 * 1024**3)
            file.flush()
            os.fsync(file.fileno())
        save('image-created.json', {'path': str(IMAGE), 'bytes': IMAGE.stat().st_size,
                                    'created': now(), 'free_bytes': capacity()})
        device = attach('attach')
        command('format', ['mkfs.ext4', '-F', '-m', '0', '-N', '1048576', '-E',
                           'nodiscard,lazy_itable_init=0,lazy_journal_init=0', str(device)], 1200)
        uuid = command('uuid', ['blkid', '-s', 'UUID', '-o', 'value', device]).strip()
        assert re.fullmatch(r'[0-9a-f-]{36}', uuid)
        command('mount-write', ['mount', '-t', 'ext4', device, str(image_view)])
        image_mounted = True
        os.chown(image_view, 1000, 1000)
        command('copy', ['runuser', '-u', 'rehearsal', '--', 'python3', '-B', str(HERE / 'worker.py'),
                         'copy', str(source_view), str(image_view / 'checkpoint')], 12720)
        command('unmount-write', ['umount', str(image_view)])
        image_mounted = False
        command('filesystem-check', ['e2fsck', '-f', '-n', device], 1200)
        command('detach-write', ['losetup', '--detach', device])
        device = None
        device = attach('reattach-readonly', True)
        assert command('uuid-reattached', ['blkid', '-s', 'UUID', '-o', 'value', device]).strip() == uuid
        command('mount-readonly', ['mount', '-t', 'ext4', '-o', 'ro,noload', device, str(image_view)])
        image_mounted = True
        command('verify', ['runuser', '-u', 'rehearsal', '--', 'python3', '-B', str(HERE / 'worker.py'),
                           'verify', str(source_view), str(image_view / 'checkpoint')], 12720)
        inputs()
        assert json.loads((HERE / 'verification.json').read_text())['pass']
        save('migration.json', {'pass': True, 'height': 15130080, 'image': str(IMAGE), 'uuid': uuid,
                               'checkpoint_subdirectory': 'checkpoint', 'source_retained': str(SOURCE),
                               'finished': now(), 'elapsed_seconds': time.monotonic() - BEGIN})
    finally:
        if image_mounted:
            command('cleanup-image-unmount', ['umount', str(image_view)])
        if device:
            command('cleanup-image-detach', ['losetup', '--detach', device])
        if source_mounted:
            command('cleanup-source-unmount', ['umount', str(source_view)])
        source_view.rmdir()
        image_view.rmdir()
        save('cleanup.json', {'finished': now(), 'mounts_removed': True, 'loop_detached': True,
                             'free_bytes': {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/w']}})

assert os.getuid() == 0
if len(sys.argv) == 1:
    inputs()
    assert json.loads((HERE / 'copy-controls.json').read_text(encoding='utf-8'))['pass']
    assert not (HERE / 'completion.json').exists() and not (HERE / 'environment.json').exists()
    os.execvp('unshare', ['unshare', '--mount', '--', 'python3', '-B', str(__file__), 'mount', os.readlink('/proc/self/ns/mnt')])
elif sys.argv[1] == 'mount':
    assert os.readlink('/proc/self/ns/mnt') != sys.argv[2]
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    old = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert old['target'] == '/'
    subprocess.run(['mount', '-t', 'drvfs', 'W:', '/mnt/w', '-o', 'uid=1000,gid=1000'], check=True)
    try:
        result = subprocess.run(['unshare', '--net', '--', 'python3', '-B', str(__file__), 'migrate', os.readlink('/proc/self/ns/net')])
    finally:
        subprocess.run(['umount', '/mnt/w'], check=True)
    save('completion.json', {'finished': now(), 'exit': result.returncode, 'verified_pass': result.returncode == 0,
                             'automatic_replay': False})
    sys.exit(result.returncode)
elif sys.argv[1] == 'migrate':
    signal.signal(signal.SIGTERM, interrupted)
    migrate()
else:
    raise RuntimeError('unknown mode')
