from pathlib import Path
import datetime
import hashlib
import json
import subprocess

here = Path(__file__).resolve().parent
assert not (here/'dispatch.json').exists() and not (here/'completion.json').exists()
for line in (here/'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
    expected,name = line.split(None,1)
    assert hashlib.sha256((here/name).read_bytes()).hexdigest() == expected,name
argv = ['C:/Users/Peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe','-NoLogo','-NoProfile','-File',str(here/'archive.ps1')]
record = {'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'mode':'cold VHD archive only; no compaction or removal','outer_timeout_seconds':36600}
with (here/'stdout.txt').open('xb') as out,(here/'stderr.txt').open('xb') as err:
    process = subprocess.Popen(argv,stdout=out,stderr=err)
    record['pid'] = process.pid
    (here/'dispatch.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('utf-8'))
    try:
        record['exit'] = process.wait(timeout=36600)
    except subprocess.TimeoutExpired:
        process.kill()
        record['exit'] = process.wait()
        record['outer_timeout'] = True
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(here/'completion.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('utf-8'))
