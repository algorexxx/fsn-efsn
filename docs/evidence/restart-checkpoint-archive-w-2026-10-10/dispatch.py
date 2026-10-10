from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

here = Path(__file__).resolve().parent
mode = sys.argv[1]
assert mode in ['archive', 'retire']
assert not (here / (mode + '-dispatch.json')).exists()
for line in (here / 'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
    expected, name = line.split(None, 1)
    assert hashlib.sha256((here / name).read_bytes()).hexdigest() == expected, name
linux = '/mnt/' + here.drive[0].lower() + here.as_posix()[2:]
argv = ['wsl.exe', '-d', 'FusionRehearsal', '-u', 'root', '--',
        'timeout', '--kill-after=20s', '7200s', 'python3', linux + '/root-launch.py', mode]
record = dict(started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              argv=argv, mode=mode, outer_seconds=7200, kill_grace_seconds=20)
with (here / (mode + '-host.stdout.txt')).open('xb') as out, (here / (mode + '-host.stderr.txt')).open('xb') as err:
    process = subprocess.Popen(argv, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid'] = process.pid
    (here / (mode + '-dispatch.json')).write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
    record['exit'] = process.wait()
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(here / (mode + '-completion.json')).write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
