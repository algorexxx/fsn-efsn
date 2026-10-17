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
monitor.require_completed_prior(config,prior)
monitor.require_manifest_files(prior,'b35b2faae777a13bbdfd07927472ed34a9dc192ddb128468d3045e924034e0f8')
report=prior/'REPORT_SHA256SUMS'
assert hashlib.sha256(report.read_bytes()).hexdigest()=='bb148262f3b76b1ebda064ef9299902b9f244beafcb358b88f64f3c055eac1b9'
for line in report.read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1)
    assert hashlib.sha256((prior/name).read_bytes()).hexdigest()==digest
outer=json.loads((prior/'storage-completion.json').read_text(encoding='utf-8'))
assert outer['exit']==0 and outer['detached'] and outer['mounts_removed']
assert json.loads((prior/'post-completion/review.json').read_text(encoding='utf-8'))['pass']
assert json.loads((prior/'post-completion/host-host-run.json').read_text(encoding='utf-8-sig'))['exit']==0
monitor.require_observer_change(config,prior/'inputs',HERE/'inputs')
monitor.require_manifest_files(HERE.parent/config['storage']['migration_bundle'],config['storage']['migration_sha256'])
for file in (HERE/'inputs').glob('*.py'):
    ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
    assert file.read_bytes()==(prior/'inputs'/file.name).read_bytes()
for line in (HERE/'inputs/SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split(None,1)
    assert hashlib.sha256((HERE/'inputs'/name).read_bytes()).hexdigest()==digest
ps=subprocess.check_output(['ps','-eo','pid,comm'],text=True)
assert not [line for line in ps.splitlines() if line.split()[-1] in ['efsn','replay-tests','observer','storage-probe']]
loops = json.loads(subprocess.check_output(['losetup','--list','--json'],text=True))['loopdevices']
assert not any(row.get('back-file') == config['storage']['image'] for row in loops)
capacity={p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
assert capacity['/home/rehearsal/results']>21*1024**3 and capacity['/mnt/d']>51*1024**3
previous=json.loads((prior/'verification.json').read_text(encoding='utf-8'))
projected=dict(previous['remaining_bytes'],**capacity)
host=json.loads((HERE/'host-preflight.json').read_text(encoding='utf-8-sig'))
assert host['mapping']=='\\\\192.168.1.250\\mnemosyne1' and host['virtual_bytes']==config['storage']['virtual_bytes']
projected['/mnt/w']=host['w_free']
required=monitor.require_starting_capacity(config,projected,previous['closed_allocated_bytes'])
record={'pass':True,'checked':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_free_bytes':capacity,
        'host_W_free_bytes':host['w_free'],'required_starting_floors':required,
        'prior_closed_allocated_bytes':previous['closed_allocated_bytes'],
        'remaining_declared_growth_bytes':config['limits']['max_bytes']-previous['closed_allocated_bytes'],
        'prior_inner_and_outer_completion_verified':True,'unchanged_controller_snapshots':True,
        'observer_only_endpoint_change_verified':True,'no_test_process_or_attachment':True,
        'image_free_is_prior_observation':True,'actual_mounted_capacity_and_cold_inventory_pending':True}
(HERE/'preflight.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
