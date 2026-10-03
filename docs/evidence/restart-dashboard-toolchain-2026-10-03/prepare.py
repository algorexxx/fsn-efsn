import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
inputs = bundle / 'inputs'
inputs.mkdir(exist_ok=False)
names = subprocess.check_output(['git', '-C', str(dashboard), 'ls-files']).decode().splitlines()
baseline = {
    'commit': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip(),
    'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names},
    'build_sha256': {p.relative_to(frontend / 'build').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (frontend / 'build').rglob('*') if p.is_file()},
}
(bundle / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8')
for name in ['package.json', 'package-lock.json']:
    (inputs / name).write_bytes((frontend / name).read_bytes())
for name in ['index.js', 'base.js', 'LICENSE']:
    (inputs / ('cra-eslint-' + name)).write_bytes((frontend / 'node_modules/eslint-config-react-app' / name).read_bytes())
packages = ['@rsbuild/core', '@rsbuild/plugin-react', '@swc/core', '@swc/jest', 'jest', 'jest-environment-jsdom', 'eslint', 'eslint-plugin-react', 'eslint-plugin-react-hooks', 'eslint-plugin-jsx-a11y', 'eslint-plugin-import', 'globals', 'confusing-browser-globals', 'acorn']
records = {}
for name in packages:
    request = urllib.request.Request('https://registry.npmjs.org/' + name, headers={'User-Agent': 'fusion-dashboard-local-review'})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read()
    data = json.loads(raw)
    selected = data['dist-tags']['latest']
    if name == 'eslint':
        selected = max((v for v in data['versions'] if v.startswith('9.') and all(n.isdigit() for n in v.split('.'))), key=lambda v: tuple(map(int, v.split('.'))))
    if name == 'acorn':
        selected = '5.7.4'
    records[name] = {'latest': data['dist-tags']['latest'], 'selected': data['versions'][selected], 'published': data['time'][selected], 'registry_sha256': hashlib.sha256(raw).hexdigest()}
    print(name, selected, records[name]['selected'].get('peerDependencies'), flush=True)
(bundle / 'registry.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
