from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
assert os.getuid() == 1000 and not (HERE/'result.json').exists()
links = subprocess.check_output(['ip', '-brief', 'link'], text=True)
assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
files = sorted((REPO/'tests/restart').glob('replay_*.py'))
before = {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
record = {'started':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'links':links,
          'uid':os.getuid(), 'python':sys.version, 'source_sha256':before,
          'source_base_commit':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
          'database_opened':False, 'scope':'Allocated-size scanner, bounded live worker, and affected controller regression checks only'}
patch = subprocess.check_output(['git','-C',str(REPO),'diff','--','tests/restart/replay_job.py','tests/restart/replay_monitor.py','tests/restart/replay_monitor_test.py','tests/restart/replay_verify.py'])
(HERE/'controller-change.patch').write_bytes(patch)
command = ['timeout','--kill-after=5s','90s',sys.executable,'-B','-m','unittest','-v','replay_monitor_test']
record['argv'] = command
with (HERE/'stdout.txt').open('xb') as out, (HERE/'stderr.txt').open('xb') as err:
    result = subprocess.run(command,cwd=REPO/'tests/restart',stdout=out,stderr=err)
record['exit'] = result.returncode
record['source_unchanged'] = before == {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
record['pass'] = result.returncode == 0 and record['source_unchanged']
(HERE/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record),flush=True)
assert record['pass']
