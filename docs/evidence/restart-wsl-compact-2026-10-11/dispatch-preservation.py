from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

here = Path(__file__).resolve().parent
phase = sys.argv[1]
assert phase in ['before', 'after']
assert not (here/phase).exists() and not (here/(phase+'-dispatch.json')).exists()
for manifest in ['ARCHIVE_OUTPUT_SHA256SUMS', 'PRESERVATION_INPUT_SHA256SUMS']:
    for line in (here/manifest).read_text(encoding='utf-8').splitlines():
        expected, name = line.split(None, 1)
        assert hashlib.sha256((here/name).read_bytes()).hexdigest() == expected, name
assert json.loads((here/'archive-verification.json').read_text(encoding='utf-8'))['pass']
assert json.loads((here/'completion.json').read_text(encoding='utf-8'))['exit'] == 0
assert not (here/'archive-failure.json').exists()
script = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-wsl-compact-2026-10-11/preservation-check.py'
argv = ['wsl.exe', '-d', 'FusionRehearsal', '-u', 'root', '--', 'timeout', '--signal=TERM', '--kill-after=30s', '123m', 'python3', script, phase]
record = {'started': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'argv': argv, 'phase': phase, 'outer_timeout_seconds': 7560, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (here/(phase+'.stdout.txt')).open('xb') as out, (here/(phase+'.stderr.txt')).open('xb') as err:
    process = subprocess.Popen(argv, stdout=out, stderr=err)
    record['pid'] = process.pid
    (here/(phase+'-dispatch.json')).write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
    try:
        record['exit'] = process.wait(timeout=7560)
    except subprocess.TimeoutExpired:
        process.kill()
        record['exit'] = process.wait()
        record['outer_timeout'] = True
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(here/(phase+'-completion.json')).write_bytes((json.dumps(record, indent=2)+'\n').encode('utf-8'))
