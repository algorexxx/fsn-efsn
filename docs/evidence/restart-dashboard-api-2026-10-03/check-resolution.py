import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
linux = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', linux + 'tmp/dashboard-runtime-review/v24.21.0/node', linux + (bundle.relative_to(root) / 'check-api-resolution.cjs').as_posix(), linux + 'tmp/fsn-stats-auth']
result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
(bundle / 'api-resolution.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode()
record = json.loads(result.stdout)
record['command'] = command
record['check_sha256'] = hashlib.sha256((bundle / 'check-api-resolution.cjs').read_bytes()).hexdigest()
(bundle / 'api-resolution.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
