from pathlib import Path
import datetime
import hashlib
import json

here=Path(__file__).resolve().parent
runtime=Path('/home/rehearsal/results')/here.name
raw=(runtime/'status.json').read_bytes()
status=json.loads(raw)
assert not (here/'completion.json').exists() and not status['failures'] and not status['stop_reason']
record={'observed':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,
        'status_sha256':hashlib.sha256(raw).hexdigest(),'scope':'Dispatch/startup observation only; actual replay has not yet been established by this observation',
        'database_files_read_or_hashed':False}
assert status['replay_pid'] is None
with (here/'startup-observation.json').open('x',encoding='utf-8') as file:file.write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
