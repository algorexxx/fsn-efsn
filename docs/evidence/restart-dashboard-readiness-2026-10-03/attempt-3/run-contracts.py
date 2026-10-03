import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
attempt = sys.argv[1]
if not re.fullmatch(r'attempt-[1-9][0-9]*', attempt):
    raise ValueError('Explicit attempt-N required')
output = evidence / attempt
output.mkdir()
capture = json.loads((evidence / 'capture.json').read_text(encoding='utf-8'))
archived = evidence / 'baseline/server.js'
harness = evidence / 'collector-contract.test.cjs'
assert hashlib.sha256(archived.read_bytes()).hexdigest() == capture['dashboard_source_sha256']['server.js']
assert hashlib.sha256(harness.read_bytes()).hexdigest() == capture['harness_sha256']
(output / 'run-contracts.py').write_bytes(Path(__file__).read_bytes())
command = ['node', '--test', '--test-reporter=tap', str(harness)]
result = subprocess.run(command, capture_output=True)
(output / 'tests.tap').write_bytes(result.stdout)
(output / 'stderr.txt').write_bytes(result.stderr)
(output / 'exit.txt').write_text(str(result.returncode) + '\n', encoding='utf-8')
(output / 'command.json').write_text(json.dumps(command, indent=2) + '\n', encoding='utf-8')
print(result.stdout.decode('utf-8'))
print(result.stderr.decode('utf-8'))
sys.exit(result.returncode)
