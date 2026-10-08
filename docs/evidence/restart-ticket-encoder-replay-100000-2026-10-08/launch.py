from pathlib import Path
import fcntl
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
TARGET = Path('/home/rehearsal/replay/candidate-ticket-encoding-100000')
SOURCE = Path('/home/rehearsal/data/efsn/chaindata')
RUN = Path('/home/rehearsal/results') / HERE.name

assert os.getuid() == 0
if len(sys.argv) == 1:
    assert not TARGET.exists() and not RUN.exists()
    os.execvp('unshare', ['unshare', '--mount', '--net', '--', 'python3', str(HERE/'launch.py'), os.readlink('/proc/self/ns/net'), os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 3
assert sys.argv[1] != os.readlink('/proc/self/ns/net') and sys.argv[2] != os.readlink('/proc/self/ns/mnt')
assert SOURCE.resolve() == SOURCE and SOURCE.is_dir() and not SOURCE.is_symlink()
assert TARGET.parent.resolve() == TARGET.parent and not TARGET.exists()
assert not RUN.exists()
assert Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').is_file()
lock = open(str(TARGET)+'.run.lock', 'a', encoding='utf-8')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
subprocess.run(['mount','--make-rprivate','/'], check=True)
mountpoint = tempfile.mkdtemp(prefix='f12-replay-source-')
closed = tempfile.mkdtemp(prefix='f12-replay-closed-')
mounted = []
result = 1
try:
    subprocess.run(['mount','--bind',str(SOURCE),mountpoint], check=True)
    mounted.append(mountpoint)
    subprocess.run(['mount','-o','remount,bind,ro',mountpoint], check=True)
    command = ['runuser','-u','rehearsal','--','python3',str(HERE/'run.py')]
    arguments = [sys.argv[1],sys.argv[2],mountpoint]
    result = subprocess.run(command+['replay']+arguments).returncode
    if result == 0:
        subprocess.run(['mount','--bind',str(TARGET),closed], check=True)
        mounted.append(closed)
        subprocess.run(['mount','-o','remount,bind,ro',closed], check=True)
        result = subprocess.run(command+['inspect']+arguments+[closed]).returncode
finally:
    if RUN.exists():
        final = subprocess.run(['runuser','-u','rehearsal','--','python3',str(HERE/'run.py'),'finalize',sys.argv[1],sys.argv[2],mountpoint])
        if final.returncode:
            result = final.returncode
    for directory in reversed(mounted):
        subprocess.run(['umount',directory], check=True)
    os.rmdir(closed)
    os.rmdir(mountpoint)
sys.exit(result)
