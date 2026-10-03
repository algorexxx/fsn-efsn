from pathlib import Path

bundle = Path(__file__).resolve().parent
previous = bundle.parent / 'restart-dashboard-frontend-2026-10-03'
for name in ['run-contracts.py', 'run-wss.py', 'check-linux-processes.py', 'check-windows-processes.ps1', 'browser-check.cjs', 'run-browser.py', 'set-browser-scenario.py', 'activate-build.ps1', 'review-compiled.py']:
    value = (previous / name).read_bytes()
    value = value.replace(b'dashboard-browser-frontend-scenario', b'dashboard-browser-toolchain-scenario')
    if name == 'activate-build.ps1':
        value = value.replace(b'dashboard-frontend-build', b'dashboard-toolchain-build').replace(b'frontend-1/result.json', b'frontend-3/result.json')
    if name == 'review-compiled.py':
        value = value.replace(b'audit-after.json', b'installed-audit.stdout.txt').replace(b'frontend-1/result.json', b'frontend-4/result.json')
    (bundle / name).write_bytes(value)
