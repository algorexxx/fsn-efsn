from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert os.getuid() == 1000 and sys.flags.optimize == 0
config = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(HERE))
import replay_monitor
replay_monitor.validate_configuration(config)
hashes = {}
for path in sorted(HERE.glob('replay_*.py')):
    ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    assert path.read_bytes() == (REPO/'tests/restart'/path.name).read_bytes()
    hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
active = []
for folder in Path('/proc').iterdir():
    if folder.name.isdigit():
        try:
            name = (folder/'comm').read_text(encoding='utf-8').strip()
            if name in ['efsn','replay-tests','observer']:
                active.append({'pid':int(folder.name),'name':name})
        except (FileNotFoundError,ProcessLookupError):
            pass
assert not active,active
record = {'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'uid':os.getuid(),'python':sys.version,'python_optimization':sys.flags.optimize,
          'kernel':subprocess.check_output(['uname','-a'],text=True).strip(),
          'source_commit':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
          'runner_sha256':hashes,'active_replay_or_node_processes':active,
          'capacity_bytes':{p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}}
target = Path('/home/rehearsal/replay')/config['target']
assert config['mode'] == 'resume' and target.is_dir()
fields = subprocess.check_output(['timeout','--kill-after=2s','15s','du','-sB1',str(target)],text=True).split()
assert len(fields) == 2 and fields[0].isdigit() and fields[1] == str(target)
record['existing_allocated_bytes'] = int(fields[0])
record['required_capacity_bytes'] = replay_monitor.require_starting_capacity(config,record['capacity_bytes'],record['existing_allocated_bytes'])
prior = REPO/'docs/evidence'/config['prior_bundle']
replay_monitor.require_verified_prior(config,json.loads((prior/'completion.json').read_text(encoding='utf-8')),json.loads((prior/'verification.json').read_text(encoding='utf-8')))
assert not (Path('/home/rehearsal/results')/config['job']).exists()
record['argv'] = ['python3','-B',str(HERE/'replay_monitor_test.py'),'-v']
with (HERE/'control-tests.stdout.txt').open('xb') as output,(HERE/'control-tests.stderr.txt').open('xb') as errors:
    record['exit'] = subprocess.run(record['argv'],cwd=HERE,stdout=output,stderr=errors).returncode
record['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(HERE/'preflight.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
assert record['exit'] == 0
