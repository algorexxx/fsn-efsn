from pathlib import Path
import os

assert os.getuid() == 0, 'Root is used only to create the network namespace.'
parent_namespace = os.readlink('/proc/self/ns/net')
runner = Path(__file__).resolve().with_name('qualify.py')
os.execvp('unshare', ['unshare', '--net', '--', 'runuser', '-u', 'rehearsal', '--', 'python3', str(runner), parent_namespace])
