import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
assert re.fullmatch(r'contracts-[1-9][0-9]*', sys.argv[1])
output = bundle / sys.argv[1]
output.mkdir(exist_ok=False)
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', runtime]
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
names = subprocess.check_output(['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', 'ls-files', '-co', '--exclude-standard']).decode().splitlines()
sources = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(set(names)) if not name.endswith('.md') and (dashboard / name).is_file()}
results = []
for name in ['test', 'test:wire']:
    label = name.replace(':', '-')
    command = prefix + ['--test', '--test-reporter=tap'] + package['scripts'][name].split()[2:]
    with (output / (label + '.stdout.txt')).open('wb') as stdout, (output / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'exit': result.returncode})
    print(name, result.returncode, flush=True)
(output / 'result.json').write_text(json.dumps({'results': results, 'source_sha256': sources}, indent=2) + '\n', encoding='utf-8', newline='\n')
raise SystemExit(any(row['exit'] != 0 for row in results))
