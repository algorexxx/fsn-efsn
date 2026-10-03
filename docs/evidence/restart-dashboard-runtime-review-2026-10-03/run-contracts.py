import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / 'node24-contracts'
output.mkdir(exist_ok=False)
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', runtime]
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
results = []
for name in ['test', 'test:wire']:
    label = name.replace(':', '-')
    with (output / (label + '.stdout.txt')).open('wb') as stdout, (output / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(prefix + package['scripts'][name].split()[1:], cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'exit': result.returncode})
(output / 'result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(results), flush=True)
raise SystemExit(any(row['exit'] != 0 for row in results))
