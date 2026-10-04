import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
output = bundle / 'install-1'
output.mkdir(exist_ok=False)
runtime = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-runtime-review/v24.21.0/node'
command = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', runtime, '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
results = []


def run(name, args):
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command + args, cwd=dashboard, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    results.append({'name': name, 'exit': result.returncode, 'command': command + args})
    (output / 'result.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(name, result.returncode, flush=True)
    assert result.returncode == 0, name


run('lock', ['install', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--engine-strict', '--no-audit', '--no-fund'])
old = (dashboard / 'node_modules').resolve()
preserved = (root / 'tmp/dashboard-mmdb-backend-before').resolve()
assert old.is_relative_to(root.resolve()) and preserved.is_relative_to(root.resolve()) and not preserved.exists()
old.rename(preserved)
assert preserved.is_dir() and not old.exists()
run('ci', ['ci', '--ignore-scripts', '--engine-strict', '--no-audit', '--no-fund'])
run('audit', ['audit', '--json'])
run('ls', ['ls', '--all', '--json'])
lock = json.loads((dashboard / 'package-lock.json').read_text(encoding='utf-8'))
assert lock['dependencies']['mmdb-lib']['version'] == '3.0.3'
assert 'geoip-lite' not in lock['dependencies']
metadata = {'package_sha256': hashlib.sha256((dashboard / 'package.json').read_bytes()).hexdigest(), 'lock_sha256': hashlib.sha256((dashboard / 'package-lock.json').read_bytes()).hexdigest(), 'preserved_installation': str(preserved), 'installed_reader': json.loads((old / 'mmdb-lib/package.json').read_text(encoding='utf-8'))['version']}
(output / 'installation.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
print(json.dumps(metadata), flush=True)
