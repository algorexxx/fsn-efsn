import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

bundle = Path(__file__).resolve().parent
repository = bundle.parents[2]
dashboard = repository / 'tmp/fsn-stats-auth'
attempt = bundle / sys.argv[1]
attempt.mkdir(exist_ok=False)
node = 'C:/Program Files/nodejs/node.exe'
files = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=dashboard).decode('utf-8').splitlines()
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(set(files))}
(attempt / 'source-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
results = []
for name in ['test', 'test:wire']:
    command = [node, *package['scripts'][name].split()[1:]]
    started = time.time()
    label = name.replace(':', '-')
    with (attempt / f'{label}.stdout.txt').open('wb') as output, (attempt / f'{label}.stderr.txt').open('wb') as error:
        result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=output, stderr=error, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'command': command, 'exit_code': result.returncode, 'seconds': time.time() - started})
    print(json.dumps(results[-1]), flush=True)
(attempt / 'results.json').write_text(json.dumps({'node': subprocess.check_output([node, '--version']).decode().strip(), 'results': results}, indent=2) + '\n', encoding='utf-8')
sys.exit(int(any(result['exit_code'] != 0 for result in results)))
