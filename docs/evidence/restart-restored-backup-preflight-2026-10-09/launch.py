from pathlib import Path
import fcntl
import hashlib
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
assert os.getuid()==0
for line in (HERE/'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1)
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest
if len(sys.argv)==1:
    os.execvp('unshare',['unshare','--mount','--net','--','python3',str(HERE/'launch.py'),os.readlink('/proc/self/ns/net'),os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv)==3
backup=Path('/home/rehearsal/data/efsn/chaindata')
assert backup.resolve()==backup and backup.is_dir() and not backup.is_symlink()
assert not (Path('/home/rehearsal/results')/HERE.name).exists()
with (backup/'LOCK').open('rb') as lock, Path('/home/rehearsal/replay/candidate-ticket-encoding-working.run.lock').open('rb') as replay_lock:
    fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    fcntl.flock(replay_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    subprocess.run(['mount','--make-rprivate','/'],check=True)
    view=tempfile.mkdtemp(prefix='f12-backup-preflight-')
    mounted=False
    try:
        subprocess.run(['mount','--bind',str(backup),view],check=True)
        mounted=True
        subprocess.run(['mount','-o','remount,bind,ro',view],check=True)
        result=subprocess.run(['runuser','-u','rehearsal','--','env','PYTHONDONTWRITEBYTECODE=1','python3',str(HERE/'run.py'),*sys.argv[1:],view]).returncode
    finally:
        if mounted: subprocess.run(['umount',view],check=True)
        os.rmdir(view)
sys.exit(result)
