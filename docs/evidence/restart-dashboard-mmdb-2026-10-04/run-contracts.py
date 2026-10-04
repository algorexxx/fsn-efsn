import json
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / ('contracts-' + sys.argv[1])
output.mkdir(exist_ok=False)
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
wsl = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--']
path = subprocess.check_output(wsl + ['printenv', 'PATH']).decode().strip()
prefix = wsl + ['env', 'PATH=' + runtime.rsplit('/', 1)[0] + ':' + path, runtime]
results = []
for name, args in [('contracts', ['/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'test']), ('wire', ['/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'run', 'test:wire'])]:
    if name == 'wire' and sys.argv[2:] == ['contracts-only']:
        continue
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(prefix + args, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'exit': result.returncode, 'command': prefix + args})
    (output / 'result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(name, result.returncode, flush=True)
assert all(result['exit'] == 0 for result in results)
