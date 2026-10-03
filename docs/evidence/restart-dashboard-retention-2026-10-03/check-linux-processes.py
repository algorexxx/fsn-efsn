import json
from pathlib import Path

remaining = []
for process in Path('/proc').iterdir():
    if not process.name.isdecimal():
        continue
    try:
        arguments = (process / 'cmdline').read_bytes().split(b'\x00')
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    executable = arguments[0].rsplit(b'/', 1)[-1] if arguments else b''
    if executable == b'dashboard-presentation-tests' or (executable == b'node' and any(b'efsn-wire-server.cjs' in value for value in arguments[1:])):
        remaining.append({'pid': int(process.name), 'arguments': [value.decode() for value in arguments if value]})
result = {'remaining_test_processes': remaining, 'count': len(remaining)}
Path(__file__).with_name('linux-process-cleanup.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
raise SystemExit(bool(remaining))
