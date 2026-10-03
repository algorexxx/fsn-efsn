import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
names = subprocess.check_output(['git', '-C', str(dashboard), 'ls-files']).decode().splitlines()
baseline = {
    'commit': subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip(),
    'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names},
    'build_sha256': {p.relative_to(dashboard / 'react-frontend/build').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (dashboard / 'react-frontend/build').rglob('*') if p.is_file()},
}
(bundle / 'baseline.json').write_text(json.dumps(baseline, indent=2) + '\n', encoding='utf-8', newline='\n')
previous = bundle.parent / 'restart-dashboard-toolchain-2026-10-03'
for name in ['run-browser.py', 'browser-check.cjs', 'set-browser-scenario.py', 'run-frontend.py', 'activate-build.ps1', 'run-wss.py', 'check-linux-processes.py', 'check-windows-processes.ps1']:
    value = (previous / name).read_bytes()
    value = value.replace(b'dashboard-browser-toolchain-scenario', b'dashboard-browser-pins-scenario')
    value = value.replace(b'dashboard-toolchain-build', b'dashboard-pins-build')
    if name == 'activate-build.ps1':
        value = value.replace(b'frontend-3/result.json', b'frontend-1/result.json')
    (bundle / name).write_bytes(value)
print('Saved baseline and reused acceptance helpers')
