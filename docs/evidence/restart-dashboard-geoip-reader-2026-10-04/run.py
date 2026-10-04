import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'


def linux(path):
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


output = bundle / 'run-1'
output.mkdir(exist_ok=False)
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'timeout', '45s', runtime, '--max-old-space-size=128', linux(bundle / 'compare.cjs')]
with (output / 'stdout.txt').open('wb') as stdout, (output / 'stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
(output / 'result.json').write_text(json.dumps({'exit': result.returncode, 'command': command}, indent=2) + '\n', encoding='utf-8')
print('exit:', result.returncode)
print((output / 'stdout.txt').read_text(encoding='utf-8'))
print((output / 'stderr.txt').read_text(encoding='utf-8')[:2500])
