import hashlib
import json
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / sys.argv[1]
output.mkdir()
mode = sys.argv[2]
assert mode in ['baseline', 'candidate']
node = 'C:/Program Files/nodejs/node.exe'
package = json.loads((dashboard / 'package.json').read_text(encoding='utf-8'))
commands = [('regression', [node, '--test', 'test/head-budget.test.cjs'])] if mode == 'baseline' else [(name.replace(':', '-'), [node, *package['scripts'][name].split()[1:]]) for name in ['test', 'test:wire']]
files = set(subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=dashboard).decode('utf-8').splitlines())
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in sorted(files)}
results = []
for name, command in commands:
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'command': command, 'exit_code': result.returncode})
    print(json.dumps(results[-1]), flush=True)
assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == value for name, value in hashes.items())
success = all(item['exit_code'] == (1 if mode == 'baseline' else 0) for item in results)
(output / 'result.json').write_bytes((json.dumps({'mode': mode, 'expected_outcome_passed': success, 'source_sha256': hashes, 'results': results}, indent=2) + '\n').encode('utf-8'))
sys.exit(0 if success else 1)
