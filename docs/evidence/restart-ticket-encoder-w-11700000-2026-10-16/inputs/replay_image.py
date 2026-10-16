from pathlib import Path
import datetime
import fcntl
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

GIB = 1024**3
ROOT = Path('/home/rehearsal/replay')
FALLBACK = ROOT / 'candidate-ticket-encoding-working'


def validate_storage(config):
    storage = config['storage']
    if set(storage) != {'kind', 'image', 'uuid', 'virtual_bytes', 'migration_bundle', 'migration_sha256'}:
        raise ValueError('unexpected image storage fields')
    if storage['kind'] != 'w-image' or config['mode'] != 'resume' or config['target'] != 'candidate-ticket-encoding-w':
        raise ValueError('image storage requires the dedicated resumed target')
    if storage['image'] != '/mnt/w/FusionRestart/replay-work-7170976-2026-10-12/replay.ext4':
        raise ValueError('unexpected working image path')
    if storage['uuid'] != '2fb12ac9-9520-4cab-9414-f1041c4d25de' or storage['virtual_bytes'] != 512*GIB:
        raise ValueError('unexpected working image identity')
    if storage['migration_bundle'] != 'restart-w-checkpoint-copy-7170976-2026-10-12' or not re.fullmatch(r'[0-9a-f]{64}', storage['migration_sha256']):
        raise ValueError('invalid migration evidence identity')


def read_mount(path):
    return json.loads(subprocess.check_output(['timeout', '--kill-after=2s', '10s', 'findmnt', '-J', '-o',
                                               'TARGET,SOURCE,FSTYPE,OPTIONS,MAJ:MIN,FSROOT', '-T', str(path)], text=True))['filesystems'][0]


def require_mounts(target, expected, mount, share, identity):
    if share['target'] != '/mnt/w' or share['source'] != 'W:' or share['fstype'] != '9p':
        raise ValueError('missing or wrong W: mount')
    if mount['target'] != str(target) or mount['fstype'] != 'ext4' or mount['fsroot'] != '/checkpoint' or 'rw' not in mount['options'].split(','):
        raise ValueError('target is not the writable image checkpoint mount')
    if mount['maj:min'] != expected['device_number'] or list(identity) != expected['directory_identity']:
        raise ValueError('mounted checkpoint identity changed')


def capacity_paths(target):
    return ['/home/rehearsal/results', '/mnt/d', '/mnt/w', str(target)]


def require_capacity(config, capacity, existing_bytes):
    validate_storage(config)
    growth = config['limits']['max_bytes'] - existing_bytes
    if existing_bytes < 0 or growth <= 0:
        raise ValueError('existing image target leaves no growth allowance')
    target = str(ROOT / config['target'])
    floors = {'/home/rehearsal/results':21*GIB, '/mnt/d':51*GIB,
              '/mnt/w':101*GIB+growth, target:21*GIB+growth}
    for path, floor in floors.items():
        if capacity[path] <= floor:
            raise ValueError('insufficient starting capacity: '+path)
    return floors


def sample_storage(config, mounted):
    target = ROOT / config['target']
    info = target.stat()
    require_mounts(target, mounted, read_mount(target), read_mount('/mnt/w'), (info.st_dev, info.st_ino))
    free = {p:shutil.disk_usage(p).free for p in capacity_paths(target)}
    for path, floor in [('/home/rehearsal/results',20),('/mnt/d',50),('/mnt/w',100),(str(target),20)]:
        if free[path] <= floor*GIB:
            raise ValueError('storage reserve reached: '+path)
    return free


def command(args, seconds=60):
    return subprocess.check_output(['timeout', '--kill-after=10s', str(seconds)+'s']+args, text=True)


def attach_image(image, uuid):
    loops = json.loads(command(['losetup','--list','--json']))['loopdevices']
    if any(row.get('back-file') == str(image) for row in loops):
        raise ValueError('image already attached')
    device = command(['losetup','--find','--show',str(image)]).strip()
    try:
        actual = json.loads(command(['losetup','--json','--output','NAME,BACK-FILE,RO',device]))['loopdevices']
        if actual != [{'name':device,'back-file':str(image),'ro':False}]:
            raise ValueError('loop backing identity differs')
        if command(['blkid','-s','UUID','-o','value',device]).strip() != uuid:
            raise ValueError('image UUID differs')
    except BaseException:
        command(['losetup','--detach',device])
        raise
    return device


def run_attached(image, uuid, target, child):
    if target.exists() or target.is_symlink() or image.is_symlink() or not stat.S_ISREG(image.stat().st_mode):
        raise ValueError('fresh target mount and regular image required')
    view = Path(tempfile.mkdtemp(prefix='f12-w-image-'))
    device = None
    image_mounted = target_mounted = target_created = False
    try:
        device = attach_image(image, uuid)
        command(['e2fsck','-f','-n',device],1200)
        command(['mount','-t','ext4',device,str(view)])
        image_mounted = True
        checkpoint = view/'checkpoint'
        if checkpoint.is_symlink() or not checkpoint.is_dir():
            raise ValueError('checkpoint missing inside image')
        target.mkdir(mode=0o700)
        target_created = True
        command(['mount','--bind',str(checkpoint),str(target)])
        target_mounted = True
        info = target.stat()
        mounted = {'device_number':read_mount(target)['maj:min'], 'directory_identity':[info.st_dev,info.st_ino],
                   'image':str(image),'uuid':uuid,'loop_device':device}
        return child(mounted)
    finally:
        if target_mounted:
            command(['umount',str(target)],300)
        if image_mounted:
            command(['umount',str(view)],300)
            command(['e2fsck','-f','-n',device],1200)
        if device:
            command(['losetup','--detach',device])
        if target_created:
            target.rmdir()
        view.rmdir()


def save(bundle, name, value):
    with (bundle/name).open('x',encoding='utf-8') as output:
        output.write(json.dumps(value,indent=2)+'\n')


def interrupted(signum, frame):
    raise TimeoutError('image controller interrupted by signal '+str(signum))


def main():
    import replay_monitor as monitor
    here = Path(__file__).resolve().parent
    bundle = here.parent
    config = json.loads((here/'config.json').read_text(encoding='utf-8'))
    monitor.validate_configuration(config)
    validate_storage(config)
    assert os.getuid() == 0 and not (bundle/'storage-completion.json').exists()
    if len(sys.argv) == 1:
        os.execvp('unshare',['unshare','--mount','--','python3','-B',str(__file__),'mounted'])
    assert sys.argv[1:] == ['mounted']
    signal.signal(signal.SIGTERM,interrupted)
    subprocess.run(['mount','--make-rprivate','/'],check=True)
    assert read_mount('/mnt/w')['target'] == '/'
    command(['mount','-t','drvfs','W:','/mnt/w','-o','uid=1000,gid=1000'])
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = 1
    try:
        storage = config['storage']
        migration = bundle.parent/storage['migration_bundle']
        monitor.require_manifest_files(migration,storage['migration_sha256'])
        assert json.loads((migration/'completion.json').read_text())['verified_pass']
        assert json.loads((migration/'review.json').read_text())['pass']
        image = Path(storage['image'])
        assert image.resolve() == image and image.stat().st_size == storage['virtual_bytes']
        assert read_mount('/mnt/w')['source'] == 'W:'
        locks = [open(ROOT/'w-image-migration.run.lock','a'),open(str(FALLBACK)+'.run.lock','a')]
        for lock in locks:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fallback_lock = (FALLBACK/'LOCK').open('rb')
        fcntl.flock(fallback_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        target = ROOT/config['target']
        def run(mounted):
            sample_storage(config,mounted)
            save(bundle,'storage-mounted.json',mounted)
            return subprocess.run(['python3','-B',str(here/'replay_launch.py')]).returncode
        result = run_attached(image,storage['uuid'],target,run)
    finally:
        command(['umount','/mnt/w'])
        save(bundle,'storage-completion.json',{'started':started,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'exit':result,'detached':True,'mounts_removed':True,'automatic_continuation':False})
    sys.exit(result)


if __name__ == '__main__':
    main()
