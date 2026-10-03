import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / 'wire-1'
output.mkdir(exist_ok=False)
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
paths = subprocess.check_output(git + ['ls-files', '-co', '--exclude-standard']).decode().splitlines()
source = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in paths if not name.endswith('.md')}
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
arguments = package['scripts']['test:wire'].split()[1:]
record = {'source_sha256': source, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'results': []}
commands = {
    'linux': ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-linux-runtime/node-v22.11.0-linux-x64/bin/node'],
    'windows': ['C:/Program Files/nodejs/node.exe'],
}
for name, command in commands.items():
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command + arguments, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    record['results'].append({'platform': name, 'exit': result.returncode})
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record['results']))
raise SystemExit(any(value['exit'] != 0 for value in record['results']))
