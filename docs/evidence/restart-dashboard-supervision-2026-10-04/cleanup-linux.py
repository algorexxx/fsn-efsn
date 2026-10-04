import json
import os
import re
import shutil
import subprocess
from pathlib import Path

assert os.geteuid() == 0
bundle = Path(__file__).resolve().parent
processes = subprocess.check_output(['ps', '-eo', 'pid=,args=']).decode().splitlines()
remaining = [line for line in processes if '/restart-dashboard-supervision-2026-10-04/reporter.cjs' in line or '/restart-dashboard-supervision-2026-10-04/log-probe.py' in line]
assert remaining == [], remaining
removed = []
machine = Path('/etc/machine-id').read_text().strip()
for name in ['run-1', 'run-2', 'run-3', 'run-4', 'journal-1']:
    record = json.loads((bundle / name / 'result.json').read_text(encoding='utf-8'))
    namespace = record['namespace']
    assert re.fullmatch(r'fsn-stats-(?:log-)?test-[0-9a-f]{8}', namespace)
    for unit in record.get('units', {}).values():
        assert not (Path('/run/systemd/system') / unit).exists()
        assert not (Path('/run/credentials') / unit).exists()
    for suffix in ['.service', '.socket']:
        state = subprocess.run(['systemctl', 'is-active', 'systemd-journald@' + namespace + suffix], stdout=subprocess.PIPE)
        assert state.returncode != 0
    if 'private' in record:
        path = Path(record['private'])
        assert path.parent.resolve() == Path('/home/rehearsal')
        assert path.name.startswith('fusion-dashboard-supervision-') and not path.is_symlink()
        assert path.resolve() == path
        assert not (path / 'data/postmaster.pid').exists()
        assert not any(str(path) in line for line in processes)
        if path.exists():
            shutil.rmtree(path)
        removed.append(str(path))
    for parent in [Path('/run/log/journal'), Path('/var/log/journal')]:
        path = parent / (machine + '.' + namespace)
        assert not path.is_symlink() and path.resolve().parent == parent.resolve()
        if path.exists():
            shutil.rmtree(path)
        removed.append(str(path))
result = {'remaining_fixture_processes': remaining, 'removed_paths': removed, 'all_removed': all(not Path(name).exists() for name in removed)}
(bundle / 'cleanup.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
