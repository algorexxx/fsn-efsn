import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
scratch = root / 'tmp/dashboard-toolchain-resolution'
scratch.mkdir(exist_ok=False)
registry = json.loads((bundle / 'registry.json').read_text(encoding='utf-8'))
manifest = json.loads((frontend / 'package.json').read_text(encoding='utf-8'))
del manifest['dependencies']['react-scripts']
del manifest['eslintConfig']
manifest['scripts'] = {'start': 'rsbuild dev --host 127.0.0.1', 'lint': 'eslint src --max-warnings=0', 'build': 'npm run lint && rsbuild build', 'test': 'jest'}
manifest['devDependencies'] = {name: item['selected']['version'] for name, item in registry.items() if name != 'acorn'}
(scratch / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(scratch / 'package-lock.json').write_bytes((frontend / 'package-lock.json').read_bytes())
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
records = []
for label, args in [('resolve', ['install', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund']), ('acorn', ['update', 'acorn', '--package-lock-only', '--lockfile-version=1', '--ignore-scripts', '--no-audit', '--no-fund']), ('audit', ['audit', '--json'])]:
    command = prefix + args
    with (bundle / (label + '.stdout.txt')).open('wb') as stdout, (bundle / (label + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(command, cwd=scratch, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': label, 'command': command, 'exit': result.returncode})
    print(label, result.returncode, flush=True)
    assert result.returncode == 0 or label == 'audit' and result.returncode == 1
(bundle / 'resolution.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
audit = json.loads((bundle / 'audit.stdout.txt').read_text(encoding='utf-8'))
print(json.dumps({'metadata': audit['metadata'], 'names': list(audit['vulnerabilities'])}, indent=2))
