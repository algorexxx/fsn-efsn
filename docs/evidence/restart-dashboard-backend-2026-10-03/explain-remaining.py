import json
import os
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
audit = json.loads((bundle / 'audit-after.json').read_text(encoding='utf-8'))
command = ['C:/Program Files/nodejs/node.exe', 'C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js', 'explain', '--json'] + sorted(audit['vulnerabilities'])
environment = dict(os.environ, npm_config_cache=str(root / 'tmp/dashboard-audit-cache'))
with (bundle / 'remaining-paths.json').open('wb') as stdout, (bundle / 'remaining-paths.stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=dashboard, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode == 0
paths = json.loads((bundle / 'remaining-paths.json').read_text(encoding='utf-8'))
assert {row['name'] for row in paths} == set(audit['vulnerabilities'])
print(json.dumps({'exit': result.returncode, 'explained_packages': len(paths)}))
