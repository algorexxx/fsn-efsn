import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
output = bundle / 'comparison-1'
output.mkdir(exist_ok=False)


def linux(path):
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


results = []
for label, script, args in [('legacy-original', 'legacy.cjs', ['original']), ('legacy-patched', 'legacy.cjs', ['patched']), ('model', 'model.cjs', [])]:
    command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'GEODATADIR=' + linux(root / 'tmp/dashboard-geoip-validation-1/precision'), 'timeout', '30s', runtime, '--max-old-space-size=128', linux(bundle / script)] + args
    with (output / (label + '.stdout.txt')).open('wb') as stdout, (output / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': label, 'exit': result.returncode, 'command': command})
    print(label, result.returncode, flush=True)
(output / 'result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
assert all(result['exit'] == 0 for result in results)
