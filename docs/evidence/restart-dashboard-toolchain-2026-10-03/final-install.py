import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
frontend = root / 'tmp/fsn-stats-auth/react-frontend'
candidate = root / 'tmp/dashboard-toolchain-resolution/package-lock.json'
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == json.loads((bundle / 'modern-lock.json').read_text(encoding='utf-8'))['sha256']
(frontend / 'package-lock.json').write_bytes(candidate.read_bytes())
prefix = json.loads((bundle / 'install.json').read_text(encoding='utf-8'))['command'][:-4]
records = []
for label, args in [('final-install', ['ci', '--ignore-scripts', '--no-audit', '--no-fund']), ('installed-audit', ['audit', '--json'])]:
    command = prefix + args
    with (bundle / (label + '.stdout.txt')).open('wb') as stdout, (bundle / (label + '.stderr.txt')).open('wb') as stderr:
        completed = subprocess.run(command, cwd=frontend, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW)
    records.append({'name': label, 'command': command, 'exit': completed.returncode})
    print(label, completed.returncode, flush=True)
    assert completed.returncode == 0
lock = json.loads((frontend / 'package-lock.json').read_text(encoding='utf-8'))
installed, omitted = [], []
for path, entry in lock['packages'].items():
    if not path:
        continue
    manifest = frontend / path / 'package.json'
    if not manifest.exists():
        assert entry.get('optional'), path
        omitted.append(path)
        continue
    data = manifest.read_bytes()
    assert json.loads(data)['version'] == entry['version'], path
    installed.append({'path': path, 'version': entry['version'], 'package_sha256': hashlib.sha256(data).hexdigest()})
diff = json.loads((bundle / 'lock-diff.json').read_text(encoding='utf-8'))
removed = [c['path'] for c in diff['changes'] if c['after'] is None]
assert all(not (frontend / path).exists() for path in removed)
record = {'commands': records, 'lock_sha256': hashlib.sha256((frontend / 'package-lock.json').read_bytes()).hexdigest(), 'installed': installed, 'omitted_optional': omitted, 'removed_paths_absent': removed}
(bundle / 'final-install.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('Installed', len(installed), 'omitted optional', len(omitted), 'removed absent', len(removed), flush=True)
