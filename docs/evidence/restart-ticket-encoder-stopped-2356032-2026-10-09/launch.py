from pathlib import Path
import fcntl
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results')/HERE.name
PATHS = [Path('/home/rehearsal/data/efsn/chaindata'), Path('/home/rehearsal/replay/candidate-ticket-encoding-2200000'), Path('/home/rehearsal/replay/candidate-ticket-encoding-2400000')]

assert os.getuid() == 0 and not RUN.exists() and not (HERE/'qualification').exists()
if len(sys.argv) == 1:
    os.execvp('unshare', ['unshare','--mount','--net','--','python3',str(HERE/'launch.py'),os.readlink('/proc/self/ns/net'),os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 3
assert sys.argv[1] != os.readlink('/proc/self/ns/net') and sys.argv[2] != os.readlink('/proc/self/ns/mnt')
for path in PATHS:
    assert path.resolve() == path and path.is_dir() and not path.is_symlink()
locks = [open(str(path)+'.run.lock','a',encoding='utf-8') for path in PATHS[1:]]
for lock in locks:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
subprocess.run(['mount','--make-rprivate','/'],check=True)
directories = [tempfile.mkdtemp(prefix='f12-stopped-'+name+'-') for name in ['source','checkpoint','closed']]
mounted = []
try:
    for path,directory in zip(PATHS,directories):
        subprocess.run(['mount','--bind',str(path),directory],check=True)
        mounted.append(directory)
        subprocess.run(['mount','-o','remount,bind,ro',directory],check=True)
    result = subprocess.run(['runuser','-u','rehearsal','--','python3',str(HERE/'run.py')]+sys.argv[1:]+directories).returncode
finally:
    for directory in reversed(mounted):
        subprocess.run(['umount',directory],check=True)
    for directory in reversed(directories):
        os.rmdir(directory)
sys.exit(result)
