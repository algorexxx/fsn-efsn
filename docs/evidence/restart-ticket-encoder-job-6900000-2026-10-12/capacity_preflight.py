from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
assert os.getuid()==1000 and len(sys.argv)==2
output=HERE/sys.argv[1]
assert output.parent==HERE and not output.exists()
sys.path.insert(0,str(HERE/'inputs'))
import replay_monitor

config=json.loads((HERE/'inputs/config.json').read_text(encoding='utf-8'))
replay_monitor.validate_configuration(config)
for file in (HERE/'inputs').glob('replay_*.py'):
    assert file.read_bytes()==(REPO/'tests/restart'/file.name).read_bytes()
prior=REPO/'docs/evidence'/config['prior_bundle']
replay_monitor.require_completed_prior(config,prior)
replay_monitor.require_observer_change(config,prior/'inputs',HERE/'inputs')
active=[]
for folder in Path('/proc').iterdir():
    if folder.name.isdigit():
        try:
            name=(folder/'comm').read_text(encoding='utf-8').strip()
            if name in ['efsn','replay-tests','observer']: active.append({'pid':int(folder.name),'name':name})
        except (FileNotFoundError,ProcessLookupError):
            pass
assert not active,active
target=Path('/home/rehearsal/replay')/config['target']
fields=subprocess.check_output(['timeout','--kill-after=2s','15s','du','-sB1',str(target)],text=True).split()
assert len(fields)==2 and fields[0].isdigit() and fields[1]==str(target)
size=int(fields[0])
free={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
record={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),'configuration':config,'existing_allocated_bytes':size,'capacity_bytes':free,'active_replay_or_node_processes':active,'prior_verified':True,'configuration_sha256':hashlib.sha256((HERE/'inputs/config.json').read_bytes()).hexdigest(),'launched':False}
try:
    record['required_capacity_bytes']=replay_monitor.require_starting_capacity(config,free,size)
    record['capacity_pass']=True
except ValueError as error:
    record['capacity_pass']=False
    record['reason']=str(error)
with output.open('x',encoding='utf-8') as file:
    json.dump(record,file,indent=2)
    file.write('\n')
print(json.dumps(record,indent=2))
sys.exit(0 if record['capacity_pass'] else 1)
