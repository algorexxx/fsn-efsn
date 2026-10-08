from pathlib import Path
import os

assert os.getuid() == 0
runner = Path(__file__).resolve().with_name('run.py')
os.execvp('unshare', ['unshare', '--net', '--', 'runuser', '-u', 'rehearsal', '--', 'python3', str(runner), os.readlink('/proc/self/ns/net')])
