from pathlib import Path
import os
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE = Path('/home/rehearsal/data/efsn/chaindata')

assert os.getuid() == 0
assert Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').is_file()
if len(sys.argv) == 1:
    os.execvp('unshare', ['unshare', '--mount', '--net', '--', 'python3', str(HERE / 'launch.py'), os.readlink('/proc/self/ns/net')])
assert len(sys.argv) == 2 and sys.argv[1] != os.readlink('/proc/self/ns/net')
subprocess.run(['mount', '--make-rprivate', '/'], check=True)
mountpoint = tempfile.mkdtemp(prefix='f12-ticket-readonly-')
try:
    subprocess.run(['mount', '--bind', str(SOURCE), mountpoint], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro', mountpoint], check=True)
    result = subprocess.run(['runuser', '-u', 'rehearsal', '--', 'python3', str(HERE / 'run.py'), sys.argv[1], mountpoint])
finally:
    subprocess.run(['umount', mountpoint], check=True)
    os.rmdir(mountpoint)
sys.exit(result.returncode)
