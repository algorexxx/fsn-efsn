from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
NAME = HERE.name
BINARY = Path('/home/rehearsal/results/restart-w-direct-probe-v2-2026-10-12/storage-probe')
BINARY_SHA = 'bc16405e3ddf4738ba80380709d15714a70641fd5054a44e74d08f4174cfb4e6'

def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as file:
        file.write(json.dumps(value, indent=2) + '\n')

def run(name, args):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(['timeout', '--kill-after=5s', '180s'] + args, capture_output=True)
    (HERE / (name + '.stdout.txt')).write_bytes(result.stdout)
    (HERE / (name + '.stderr.txt')).write_bytes(result.stderr)
    save(name + '.json', {'started': start, 'argv': args, 'exit': result.returncode,
                         'finished': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    if result.returncode:
        raise RuntimeError(name + ' failed; see recorded stderr')
    return result.stdout.decode('utf-8')

def inside():
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    interfaces = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(interfaces) == 1 and interfaces[0]['ifname'] == 'lo' and 'UP' not in interfaces[0]['flags']
    assert hashlib.sha256(BINARY.read_bytes()).hexdigest() == BINARY_SHA
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert mount['target'] == '/mnt/w' and mount['source'] == 'W:' and mount['fstype'] == '9p'
    free = {p: shutil.disk_usage(p).free for p in ['/home/rehearsal', '/mnt/d', '/mnt/w']}
    for path, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
        assert free[path] > gib * 1024**3
    save('environment.json', {'interfaces': interfaces, 'mount': mount, 'free_before': free,
         'binary_sha256': BINARY_SHA, 'parent_netns': sys.argv[2], 'netns': os.readlink('/proc/self/ns/net')})
    local = Path('/home/rehearsal/results') / NAME
    local.mkdir()
    os.chown(local, 1000, 1000)
    run('local-control', ['runuser', '-u', 'rehearsal', '--', str(BINARY), 'probe', str(local / 'db')])
    root = Path('/mnt/w/FusionRestart') / NAME
    assert root.parent.resolve() == root.parent and root.parent.is_dir()
    root.mkdir()
    image = root / 'disposable.ext4'
    with image.open('xb') as file:
        file.truncate(256 * 1024**2)
        file.flush()
        os.fsync(file.fileno())
    save('image.json', {'path': str(image), 'length': image.stat().st_size})
    loop = run('attach', ['losetup', '--find', '--show', str(image)]).strip()
    assert re.fullmatch(r'/dev/loop[0-9]+', loop)
    point = Path(tempfile.mkdtemp(prefix=NAME + '-'))
    mounted = False
    try:
        identity = json.loads(run('loop-identity', ['losetup', '--json', '--output', 'NAME,BACK-FILE', loop]))
        assert identity['loopdevices'] == [{'name': loop, 'back-file': str(image)}]
        run('format', ['mkfs.ext4', '-F', '-E', 'lazy_itable_init=0,lazy_journal_init=0', loop])
        run('mount', ['mount', '-t', 'ext4', loop, str(point)])
        mounted = True
        os.chown(point, 1000, 1000)
        run('database', ['runuser', '-u', 'rehearsal', '--', str(BINARY), 'probe', str(point / 'db')])
        run('unmount', ['umount', str(point)])
        mounted = False
        run('filesystem-check', ['e2fsck', '-f', '-n', loop])
        save('result.json', {'status': 'pass', 'scope': 'local control and W-backed ext4 image synthetic DB checks',
              'limits': '256 MiB disposable image; 32 MiB logical DB writes',
              'limitations': 'not full replay throughput, power loss, disconnected storage or a qualified migration'})
    finally:
        if mounted:
            run('cleanup-unmount', ['umount', str(point)])
        run('detach', ['losetup', '--detach', loop])
        point.rmdir()

assert os.getuid() == 0
if len(sys.argv) == 1:
    os.execvp('unshare', ['unshare', '--mount', '--', 'python3', '-B', str(__file__), 'mount', os.readlink('/proc/self/ns/mnt')])
elif sys.argv[1] == 'mount':
    assert os.readlink('/proc/self/ns/mnt') != sys.argv[2]
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    old = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert old['target'] == '/'
    subprocess.run(['mount', '-t', 'drvfs', 'W:', '/mnt/w', '-o', 'uid=1000,gid=1000'], check=True)
    try:
        result = subprocess.run(['unshare', '--net', '--', 'python3', '-B', str(__file__), 'inside', os.readlink('/proc/self/ns/net')])
    finally:
        subprocess.run(['umount', '/mnt/w'], check=True)
    sys.exit(result.returncode)
elif sys.argv[1] == 'inside':
    inside()
else:
    raise RuntimeError('unknown mode')
