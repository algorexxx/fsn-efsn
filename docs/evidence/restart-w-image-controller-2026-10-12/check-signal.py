from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'tests/restart'))
import replay_image as image

if len(sys.argv)==1:
    os.execvp('unshare',['unshare','--mount','--','python3','-B',str(__file__),'mount'])
assert os.getuid()==0
subprocess.run(['mount','--make-rprivate','/'],check=True)
assert image.read_mount('/mnt/w')['target']=='/'
image.command(['mount','-t','drvfs','W:','/mnt/w','-o','uid=1000,gid=1000'])
try:
    backing=Path('/mnt/w/FusionRestart/restart-w-image-controller-2026-10-12/fixture.ext4')
    uuid=image.command(['blkid','-p','-s','UUID','-o','value',str(backing)]).strip()
    base=Path(tempfile.mkdtemp(prefix='w-controller-signal-'))
    target=base/'target'
    signal.signal(signal.SIGTERM,image.interrupted)
    def child(mounted):
        assert (target/'marker').read_bytes()==b'bounded-controller-fixture\n'
        os.kill(os.getpid(),signal.SIGTERM)
    try:
        image.run_attached(backing,uuid,target,child)
    except TimeoutError as error:
        assert 'signal 15' in str(error)
    else:
        raise AssertionError('SIGTERM not propagated')
    assert not target.exists()
    assert not [row for row in json.loads(image.command(['losetup','--list','--json']))['loopdevices'] if row.get('back-file')==str(backing)]
    base.rmdir()
finally:
    image.command(['umount','/mnt/w'])
record={'pass':True,'real_SIGTERM_raised_and_cleanup_completed':True,'controller_sha256':hashlib.sha256(Path(image.__file__).read_bytes()).hexdigest()}
(HERE/'signal.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
