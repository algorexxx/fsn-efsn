from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys

here = Path(__file__).resolve().parent
assert os.getuid() == 0 and not (here/'trim.json').exists()
if len(sys.argv) == 1:
    os.execvp('unshare', ['unshare', '--mount', '--net', '--', 'python3', str(here/'trim.py'), os.readlink('/proc/self/ns/net'), os.readlink('/proc/self/ns/mnt')])
assert len(sys.argv) == 3
assert sys.argv[1] != os.readlink('/proc/self/ns/net') and sys.argv[2] != os.readlink('/proc/self/ns/mnt')
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pass': False, 'commands': []}
try:
    for manifest in ['ARCHIVE_OUTPUT_SHA256SUMS', 'BEFORE_OUTPUT_SHA256SUMS', 'NATIVE_INPUT_SHA256SUMS']:
        for line in (here/manifest).read_text(encoding='utf-8').splitlines():
            expected, name = line.split(None, 1)
            assert hashlib.sha256((here/name).read_bytes()).hexdigest() == expected, name
    assert json.loads((here/'before/verification.json').read_text(encoding='utf-8'))['pass']
    assert json.loads((here/'before-completion.json').read_text(encoding='utf-8'))['exit'] == 0
    links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    record['links'] = links
    for folder in Path('/proc').iterdir():
        if folder.name.isdigit():
            try:
                assert (folder/'comm').read_text(encoding='utf-8').strip() not in ['efsn', 'replay-tests', 'restart-tests', 'observer']
            except (FileNotFoundError, ProcessLookupError):
                pass
    paths = [Path('/home/rehearsal/data/efsn/chaindata'), *[Path('/home/rehearsal/replay')/name for name in ['baseline-mainnet-3300000', 'baseline-mainnet-3600000', 'candidate-ticket-encoding-working', 'candidate-ticket-encoding-2400000-v2']]]
    for path in paths:
        assert path.resolve() == path and path.is_dir() and not path.is_symlink()
    run_locks = [open(str(p)+'.run.lock', 'a', encoding='utf-8') for p in paths[-2:]]
    for lock in run_locks:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    locks = [(p/'LOCK').open('rb') for p in paths]
    for lock in locks:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
    record['locks_acquired'] = True
    record['free_before'] = {p: shutil.disk_usage(p).free for p in ['/', '/mnt/d', '/mnt/c']}
    assert record['free_before']['/'] > 20*1024**3 and record['free_before']['/mnt/d'] > 50*1024**3 and record['free_before']['/mnt/c'] > 5*1024**3
    device = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
    assert int(subprocess.check_output(['blockdev', '--getsize64', device], text=True)) == 220*1024**3
    record['root_device'] = device
    for name, argv in [('sync', ['timeout', '120s', 'sync', '-f', '/']), ('trim', ['timeout', '--kill-after=20s', '300s', 'fstrim', '--verbose', '/'])]:
        result = subprocess.run(argv, capture_output=True, timeout=350)
        (here/(name+'-operation.stdout.txt')).write_bytes(result.stdout)
        (here/(name+'-operation.stderr.txt')).write_bytes(result.stderr)
        record['commands'].append({'name': name, 'argv': argv, 'exit': result.returncode})
        assert result.returncode == 0, name
    record['free_after'] = {p: shutil.disk_usage(p).free for p in ['/', '/mnt/d', '/mnt/c']}
    record['pass'] = True
finally:
    record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (here/'trim.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
