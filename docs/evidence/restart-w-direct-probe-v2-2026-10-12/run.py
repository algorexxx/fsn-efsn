from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NAME = HERE.name
RUNTIME = Path('/home/rehearsal/results') / NAME

def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, indent=2) + '\n')

def run(name, args, **kwargs):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (HERE / (name + '.stdout.txt')).open('xb') as output, (HERE / (name + '.stderr.txt')).open('xb') as error:
        result = subprocess.run(args, stdout=output, stderr=error, **kwargs)
    save(name + '.json', {'started': started, 'argv': args, 'exit': result.returncode,
                         'finished': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    if result.returncode:
        raise RuntimeError(name + ' failed, see recorded stderr')

def probe():
    assert os.getuid() == 1000
    assert os.readlink('/proc/self/ns/net') != sys.argv[2]
    interfaces = json.loads(subprocess.check_output(['ip', '-j', 'link', 'show'], text=True))
    assert len(interfaces) == 1 and interfaces[0]['ifname'] == 'lo'
    assert 'LOOPBACK' in interfaces[0]['flags'] and 'UP' not in interfaces[0]['flags']
    mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert mount['target'] == '/mnt/w' and mount['source'] == 'W:' and mount['fstype'] == '9p'
    capacity = {str(p): shutil.disk_usage(p).free for p in [Path('/home/rehearsal'), Path('/mnt/d'), Path('/mnt/w')]}
    for p, gib in [('/home/rehearsal', 20), ('/mnt/d', 50), ('/mnt/w', 100)]:
        assert capacity[p] > gib * 1024**3, p
    root = Path('/mnt/w/FusionRestart')
    assert root.resolve() == root and root.is_dir()
    target = root / NAME
    assert not target.exists() and not RUNTIME.exists()
    RUNTIME.mkdir()
    save('environment.json', {'mount': mount, 'free_before': capacity,
         'netns': os.readlink('/proc/self/ns/net'), 'parent_netns': sys.argv[2],
         'kernel': os.uname().release, 'interfaces': interfaces,
         'target': str(target), 'scope': 'disposable synthetic data only; no blockchain DB opened'})
    env = dict(os.environ, GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local', GOWORK='off',
               GOCACHE='/home/rehearsal/.cache/go-build', GOPATH='/home/rehearsal/go',
               GOFLAGS='-mod=readonly', GOENV='off', CGO_ENABLED='0')
    binary = RUNTIME / 'storage-probe'
    run('build', ['timeout', '--kill-after=5s', '90s', '/opt/fusion-toolchain/go/bin/go', 'build',
                 '-o', str(binary), str(HERE / 'probe.go')], cwd='/home/rehearsal/fsn-efsn', env=env)
    run('build-info', ['/opt/fusion-toolchain/go/bin/go', 'version', '-m', str(binary)])
    save('binary.json', {'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()})
    target.mkdir()
    run('database', ['timeout', '--kill-after=5s', '180s', str(binary), 'probe', str(target / 'db')])
    save('result.json', {'status': 'pass', 'free_after': shutil.disk_usage('/mnt/w').free,
                        'limits': '32 MiB logical data, 180 seconds database runtime; synthetic only',
                        'limitations': 'not a chain replay, power-loss, server-cache, disconnect or throughput qualification'})

if len(sys.argv) == 1:
    assert os.getuid() == 0
    os.execvp('unshare', ['unshare', '--mount', '--', 'python3', '-B', str(__file__),
                          'mounted', os.readlink('/proc/self/ns/mnt')])
elif sys.argv[1] == 'mounted':
    assert os.getuid() == 0 and os.readlink('/proc/self/ns/mnt') != sys.argv[2]
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    old = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE', '-T', '/mnt/w'], text=True))['filesystems'][0]
    assert old['target'] == '/'
    subprocess.run(['mount', '-t', 'drvfs', 'W:', '/mnt/w', '-o', 'uid=1000,gid=1000'], check=True)
    try:
        result = subprocess.run(['unshare', '--net', '--', 'runuser', '-u', 'rehearsal', '--',
                                 'python3', '-B', str(__file__), 'probe', os.readlink('/proc/self/ns/net')])
    finally:
        subprocess.run(['umount', '/mnt/w'], check=True)
    sys.exit(result.returncode)
elif sys.argv[1] == 'probe':
    probe()
else:
    raise RuntimeError('unknown mode')
