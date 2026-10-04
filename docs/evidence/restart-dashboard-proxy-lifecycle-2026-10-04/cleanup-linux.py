import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

assert os.geteuid() == 0
bundle = Path(__file__).resolve().parent
native = json.loads((bundle / 'stationary-1/result.json').read_text(encoding='utf-8'))
private = Path(native['linux_scratch'])
assert private.parent == Path('/home/rehearsal') and private.name.startswith('fusion-dashboard-tls-')
assert not private.is_symlink() and private.resolve() == private
assert not (private / 'data/postmaster.pid').exists()
processes = subprocess.check_output(['ps', '-eo', 'pid=,args=']).decode().splitlines()
remaining = [line for line in processes if str(private) in line or '/restart-dashboard-proxy-lifecycle-2026-10-04/backend.cjs' in line or '/restart-dashboard-proxy-lifecycle-2026-10-04/reporter.cjs' in line or '/tmp/dashboard-mining-fixed-tests' in line or '/tmp/fsn-stats-auth/test/fixtures/' in line]
assert remaining == [], remaining
if private.exists():
    shutil.rmtree(private)
result = {'remaining_fixture_processes': remaining, 'native_database_directory_removed': not private.exists(), 'removed_path': str(private), 'host_tool_sha256': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ['/usr/sbin/logrotate', '/usr/bin/systemctl', '/usr/bin/openssl', '/usr/bin/gzip']}}
(bundle / 'cleanup.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
