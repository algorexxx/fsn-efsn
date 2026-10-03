import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
remaining = []
for process in Path('/proc').iterdir():
    if not process.name.isdecimal():
        continue
    try:
        arguments = (process / 'cmdline').read_bytes().split(b'\x00')
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    executable = arguments[0].rsplit(b'/', 1)[-1] if arguments else b''
    target = executable == b'dashboard-tls-tests' or executable.startswith(b'nginx')
    target = target or (executable == b'node' and any(b'efsn-wire-server.cjs' in value for value in arguments[1:]))
    target = target or (executable.startswith(b'postgres') and any(b'fusion-dashboard-tls-' in value for value in arguments))
    if target:
        remaining.append({'pid': int(process.name), 'arguments': [value.decode() for value in arguments if value]})
directories = []
for index in range(1, 5):
    result = json.loads((bundle / f'attempt-{index}/result.json').read_text(encoding='utf-8'))
    scratch = Path(result['linux_scratch'])
    directories.append({'attempt': index, 'postgres_pid_absent': not (scratch / 'data/postmaster.pid').exists(), 'private_removed': all(not (scratch / name).exists() for name in ['ca.key', 'ca.crt', 'server.key', 'server.crt', 'server.csr', 'public.pem', 'pgpass'])})
result = {'remaining_test_processes': remaining, 'count': len(remaining), 'directories': directories}
(bundle / 'linux-process-cleanup.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
raise SystemExit(bool(remaining) or not all(row['postgres_pid_absent'] and row['private_removed'] for row in directories))
