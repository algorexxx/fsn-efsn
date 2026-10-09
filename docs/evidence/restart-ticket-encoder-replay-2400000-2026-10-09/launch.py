from pathlib import Path
import fcntl
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
TARGET = Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000')
CHECKPOINT = Path('/home/rehearsal/replay/candidate-ticket-encoding-2200000')
SOURCE = Path('/home/rehearsal/data/efsn/chaindata')
RUN = Path('/home/rehearsal/results')/HERE.name

assert os.getuid() == 0
if len(sys.argv) == 1:
    assert not TARGET.exists() and not RUN.exists()
    os.execvp('unshare',['unshare','--mount','--net','--','python3',str(HERE/'launch.py'),os.readlink('/proc/self/ns/net'),os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 3
assert sys.argv[1] != os.readlink('/proc/self/ns/net') and sys.argv[2] != os.readlink('/proc/self/ns/mnt')
for path in [SOURCE,CHECKPOINT]:
    assert path.resolve() == path and path.is_dir() and not path.is_symlink()
assert TARGET.parent.resolve() == TARGET.parent and not TARGET.exists() and not RUN.exists()
assert Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').is_file()
locks = [open(str(path)+'.run.lock','a',encoding='utf-8') for path in [CHECKPOINT,TARGET]]
for lock in locks:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
subprocess.run(['mount','--make-rprivate','/'],check=True)
directories = [tempfile.mkdtemp(prefix='f12-range-'+name+'-') for name in ['source','checkpoint','closed']]
source,checkpoint,closed = directories
mounted = []
result = 1
try:
    for path,mountpoint in [(SOURCE,source),(CHECKPOINT,checkpoint)]:
        subprocess.run(['mount','--bind',str(path),mountpoint],check=True)
        mounted.append(mountpoint)
        subprocess.run(['mount','-o','remount,bind,ro',mountpoint],check=True)
    command = ['runuser','-u','rehearsal','--','python3',str(HERE/'run.py')]
    args = [sys.argv[1],sys.argv[2],source,checkpoint]
    result = subprocess.run(command+['replay']+args).returncode
    if result == 0:
        subprocess.run(['mount','--bind',str(TARGET),closed],check=True)
        mounted.append(closed)
        subprocess.run(['mount','-o','remount,bind,ro',closed],check=True)
        result = subprocess.run(command+['inspect']+args+[closed]).returncode
finally:
    if RUN.exists():
        final = subprocess.run(['runuser','-u','rehearsal','--','python3',str(HERE/'run.py'),'finalize',sys.argv[1],sys.argv[2],source,checkpoint])
        if final.returncode:
            result = final.returncode
    for directory in reversed(mounted):
        subprocess.run(['umount',directory],check=True)
    for directory in reversed(directories):
        os.rmdir(directory)
sys.exit(result)
