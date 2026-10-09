from pathlib import Path
import json
import os
import subprocess
import sys

here = Path(__file__).resolve().parent
assert os.getuid() == 0
if len(sys.argv) == 2:
    assert sys.argv[1] in ['archive', 'retire']
    os.execvp('unshare', ['unshare', '--mount', '--', 'python3', str(here/'root-launch.py'), '--inside', sys.argv[1], os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 4 and sys.argv[1] == '--inside'
assert os.readlink('/proc/self/ns/mnt') != sys.argv[3]
mode = sys.argv[2]
assert mode in ['archive', 'retire']
subprocess.run(['mount', '--make-rprivate', '/'], check=True)
assert Path('/mnt/w').resolve() == Path('/mnt/w') and Path('/mnt/w').is_dir()
mount = json.loads(subprocess.check_output(['findmnt', '-J', '-o', 'TARGET,SOURCE,FSTYPE', '-T', '/mnt/w'], text=True))['filesystems'][0]
assert mount['target'] == '/' or (mount['target'] == '/mnt/w' and mount['source'] == 'W:')
created = mount['target'] != '/mnt/w'
if created:
    subprocess.run(['mount', '-t', 'drvfs', 'W:', '/mnt/w', '-o', 'uid=1000,gid=1000'], check=True)
try:
    result = subprocess.run(['runuser', '-u', 'rehearsal', '--', 'python3', str(here/'launch.py'), mode]).returncode
finally:
    if created:
        subprocess.run(['umount', '/mnt/w'], check=True)
sys.exit(result)
