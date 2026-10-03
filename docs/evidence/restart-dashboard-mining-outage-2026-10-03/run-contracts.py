import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
output = bundle / 'contracts-1'
output.mkdir(exist_ok=False)
names = subprocess.check_output(['git', '-C', str(dashboard), '-c', 'core.autocrlf=false', 'ls-files', '-co', '--exclude-standard']).decode().splitlines()
record = {'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(set(names)) if not name.endswith('.md')}, 'results': []}
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
for name in ['test', 'test:wire']:
    output_name = name.replace(':', '-')
    with (output / (output_name + '.stdout.txt')).open('wb') as stdout, (output / (output_name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(['C:/Program Files/nodejs/node.exe'] + package['scripts'][name].split()[1:], cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    record['results'].append({'name': name, 'exit': result.returncode})
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record['results']))
raise SystemExit(any(value['exit'] != 0 for value in record['results']))
