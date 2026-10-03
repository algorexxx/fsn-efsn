import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-toolchain-resolution'
manifest = json.loads((scratch / 'package.json').read_text(encoding='utf-8'))
manifest['devDependencies'] = {k: v for k, v in manifest['devDependencies'].items() if k.startswith(('@rsbuild/', '@swc/')) or k in ['jest', 'jest-environment-jsdom']}
manifest['devDependencies']['oxlint'] = json.loads((bundle / 'oxlint-registry.json').read_text(encoding='utf-8'))['version']
manifest['scripts']['lint'] = 'oxlint src --max-warnings=0'
(scratch / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
records = []
for label, args in [('refine', ['install', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund']), ('yaml', ['update', 'js-yaml', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund']), ('audit-final', ['audit', '--json'])]:
    command = prefix + args
    with (bundle / (label + '.stdout.txt')).open('wb') as stdout, (bundle / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=scratch, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': label, 'command': command, 'exit': result.returncode})
    print(label, result.returncode, flush=True)
    assert result.returncode == 0 or label == 'audit-final' and result.returncode == 1
(bundle / 'refinement.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
audit = json.loads((bundle / 'audit-final.stdout.txt').read_text(encoding='utf-8'))
print(json.dumps(audit['metadata']))
