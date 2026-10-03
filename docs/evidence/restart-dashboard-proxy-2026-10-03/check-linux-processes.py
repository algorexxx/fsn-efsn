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
    target = executable.startswith(b'nginx') or (executable == b'node' and any(b'wire-server.cjs' in value or b'wire.test.cjs' in value or b'proxy-tls.test.cjs' in value for value in arguments[1:]))
    if target:
        remaining.append({'pid': int(process.name), 'arguments': [value.decode() for value in arguments if value]})
result = {'remaining_test_processes': remaining, 'count': len(remaining)}
Path(__file__).with_name('linux-process-cleanup.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
raise SystemExit(bool(remaining))
