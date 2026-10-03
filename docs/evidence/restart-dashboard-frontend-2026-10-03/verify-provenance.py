import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
scratch = root / 'tmp/dashboard-axios-provenance'
scratch.mkdir(exist_ok=False)
(scratch / 'package.json').write_text('{"private":true,"dependencies":{"axios":"0.34.0"}}\n', encoding='utf-8', newline='\n')
linux_root = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/'
prefix = ['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'env', 'npm_config_cache=' + linux_root + 'tmp/dashboard-audit-cache', 'npm_config_engine_strict=true', linux_root + 'tmp/dashboard-runtime-review/v24.21.0/node', '/mnt/c/Program Files/nodejs/node_modules/npm/bin/npm-cli.js']
commands = []
for name, args in [('provenance-install', ['install', '--ignore-scripts', '--no-audit', '--no-fund', '--registry=https://registry.npmjs.org']), ('provenance-check', ['audit', 'signatures', '--registry=https://registry.npmjs.org'])]:
    with (bundle / (name + '.stdout.txt')).open('wb') as stdout, (bundle / (name + '.stderr.txt')).open('wb') as stderr:
        result = subprocess.run(prefix + args, cwd=scratch, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    commands.append({'command': prefix + args, 'exit': result.returncode})
    print(name, result.returncode, flush=True)
    assert result.returncode == 0
lock = json.loads((scratch / 'package-lock.json').read_text(encoding='utf-8'))
selected = json.loads((bundle / 'axios-selected.json').read_text(encoding='utf-8'))
assert lock['packages']['node_modules/axios']['integrity'] == selected['dist']['integrity']
(bundle / 'provenance-lock.json').write_bytes((scratch / 'package-lock.json').read_bytes())
(bundle / 'provenance.json').write_text(json.dumps({'commands': commands, 'axios': '0.34.0', 'integrity_matches_selected': True}, indent=2) + '\n', encoding='utf-8', newline='\n')
