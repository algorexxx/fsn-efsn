from pathlib import Path
import ast
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'inputs'))
import replay_monitor as monitor

config=json.loads((HERE/'inputs/config.json').read_text(encoding='utf-8'))
monitor.validate_configuration(config)
prior=HERE.parent/config['prior_bundle']
monitor.require_observer_change(config,prior,HERE/'inputs')
monitor.require_verified_stopped(config,json.loads((prior/'qualification/run.json').read_text()),json.loads((prior/'verification.json').read_text()),json.loads((HERE.parent/config['stopped_attempt']/'completion.json').read_text()))
monitor.require_manifest_files(HERE.parent/config['storage']['migration_bundle'],config['storage']['migration_sha256'])
for file in (HERE/'inputs').glob('*.py'):
    ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
    assert file.read_bytes()==(HERE.parents[2]/'tests/restart'/file.name).read_bytes()
for line in (HERE/'inputs/SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1)
    assert hashlib.sha256((HERE/'inputs'/name).read_bytes()).hexdigest()==digest
processes=subprocess.check_output(['ps','-eo','pid,comm'],text=True)
assert not [line for line in processes.splitlines() if line.split()[-1] in ['efsn','replay-tests','observer','storage-probe']]
assert not json.loads(subprocess.check_output(['losetup','--list','--json'],text=True))['loopdevices']
capacity={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
assert capacity['/home/rehearsal/results']>21*1024**3 and capacity['/mnt/d']>51*1024**3
result={'pass':True,'checked':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capacity':capacity,
        'stopped_provenance_verified':True,'migration_evidence_verified':True,'observer_change_verified':True,
        'snapshots_and_syntax_verified':True,'no_test_process_or_attachment':True,
        'mounted_capacity_and_cold_inventory_pending':True,
        'initial_host_attempt':'Windows Python could not import Linux-only fcntl; no database was opened. This preflight runs under WSL.'}
(HERE/'preflight.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
