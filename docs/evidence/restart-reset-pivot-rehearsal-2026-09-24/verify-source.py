import hashlib
from pathlib import Path

workspace = Path('/mnt/c/Users/Peter/Documents/CODING/fsn-efsn')
export = Path('/home/rehearsal/fsn-efsn-reset-pivot-rehearsal')
paths = (
    'core/blockchain.go',
    'core/headerchain.go',
    'tests/restart/crash_test.go',
    'tests/restart/reset_pivot_test.go',
    'tests/restart/anchor_enforcement_test.go',
)
for relative in paths:
    local = (workspace / relative).read_bytes()
    linux = (export / relative).read_bytes()
    normalized = linux.replace(b'\r\n', b'\n')
    assert local.replace(b'\r\n', b'\n') == normalized, relative
    if relative.startswith('tests/'):
        assert local == linux, relative
    print(f'{hashlib.sha256(normalized).hexdigest()}  {relative}  byte_identical={local == linux}  LF_normalized_match=True')
