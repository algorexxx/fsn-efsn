from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'tests/restart'))
import replay_image as image

assert os.getuid() == 0
if len(sys.argv) == 1:
    os.execvp('unshare',['unshare','--mount','--','python3','-B',str(__file__),'mount'])
if sys.argv[1] == 'mount':
    subprocess.run(['mount','--make-rprivate','/'],check=True)
    assert image.read_mount('/mnt/w')['target'] == '/'
    image.command(['mount','-t','drvfs','W:','/mnt/w','-o','uid=1000,gid=1000'])
    try:
        result = subprocess.run(['unshare','--net','--','python3','-B',str(__file__),'check']).returncode
    finally:
        image.command(['umount','/mnt/w'])
    sys.exit(result)
assert sys.argv[1] == 'check'
links = json.loads(subprocess.check_output(['ip','-j','link'],text=True))
assert len(links)==1 and links[0]['ifname']=='lo' and 'UP' not in links[0]['flags']
assert image.read_mount('/mnt/w')['source']=='W:'
root = Path('/mnt/w/FusionRestart/restart-w-image-controller-2026-10-12')
assert not root.exists()
root.mkdir()
backing = root/'fixture.ext4'
with backing.open('xb') as output:
    output.truncate(64*1024**2)
    output.flush()
    os.fsync(output.fileno())
device = image.command(['losetup','--find','--show',str(backing)]).strip()
try:
    identity = json.loads(image.command(['losetup','--json','--output','NAME,BACK-FILE,RO',device]))
    assert identity['loopdevices']==[{'name':device,'back-file':str(backing),'ro':False}]
    image.command(['mkfs.ext4','-F','-m','0','-E','nodiscard,lazy_itable_init=0,lazy_journal_init=0',device])
    uuid = image.command(['blkid','-s','UUID','-o','value',device]).strip()
    seed = Path(tempfile.mkdtemp(prefix='w-controller-seed-'))
    try:
        image.command(['mount','-t','ext4',device,str(seed)])
        (seed/'checkpoint').mkdir()
    finally:
        image.command(['umount',str(seed)])
        seed.rmdir()
finally:
    image.command(['losetup','--detach',device])
base = Path(tempfile.mkdtemp(prefix='w-controller-target-'))
target = base/'target'
def require_detached():
    assert not target.exists()
    assert not [row for row in json.loads(image.command(['losetup','--list','--json']))['loopdevices'] if row.get('back-file')==str(backing)]

try:
    image.run_attached(backing,'00000000-0000-0000-0000-000000000000',target,lambda mounted: (_ for _ in ()).throw(AssertionError('child must not start')))
except ValueError as error:
    assert 'UUID differs' in str(error)
else:
    raise AssertionError('wrong UUID accepted')
require_detached()

def interrupted_child(mounted):
    info=target.stat()
    image.require_mounts(target,mounted,image.read_mount(target),image.read_mount('/mnt/w'),(info.st_dev,info.st_ino))
    with (target/'marker').open('xb') as output:
        output.write(b'bounded-controller-fixture\n')
        output.flush()
        os.fsync(output.fileno())
    raise RuntimeError('deliberate fixture interruption')

try:
    image.run_attached(backing,uuid,target,interrupted_child)
except RuntimeError as error:
    assert str(error)=='deliberate fixture interruption'
else:
    raise AssertionError('interruption not propagated')
require_detached()

def successful_child(mounted):
    assert (target/'marker').read_bytes()==b'bounded-controller-fixture\n'
    return 0

assert image.run_attached(backing,uuid,target,successful_child)==0
require_detached()
base.rmdir()
record={'pass':True,'wrong_uuid_refused_before_child':True,'exception_cleanup_detached':True,
        'fresh_reattachment_preserves_marker':True,'success_cleanup_detached':True,
        'fixture_retained':str(backing),'fixture_virtual_bytes':64*1024**2,'interfaces':links,
        'controller_sha256':hashlib.sha256(Path(image.__file__).read_bytes()).hexdigest()}
with (HERE/'lifecycle.json').open('x',encoding='utf-8') as output:
    output.write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
