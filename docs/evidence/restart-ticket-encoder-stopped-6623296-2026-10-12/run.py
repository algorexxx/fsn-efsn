from pathlib import Path
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUN = Path('/home/rehearsal/results')/HERE.name
ATTEMPT = HERE.parent/'restart-ticket-encoder-job-6900000-2026-10-12'
PRIOR_RUN = Path('/home/rehearsal/results')/ATTEMPT.name
BASE = HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08'
REPLAY_SHA = 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'
module = importlib.util.spec_from_file_location('sealed_helpers',BASE/'run.py')
r = importlib.util.module_from_spec(module)
module.loader.exec_module(r)
r.HERE,r.RUN = HERE,RUN
original_execute = r.execute


def execute_with_reserve(name, argv, cwd, env):
    free = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    r.record.setdefault('command_capacity', []).append({'name':name,'time':r.now(),'free_bytes':free})
    assert free['/home/rehearsal/results'] > 20*1024**3 and free['/mnt/d'] > 50*1024**3
    r.save()
    original_execute(name, argv, cwd, env)


r.execute = execute_with_reserve


def inspect(backup,checkpoint,closed):
    prior = json.loads((ATTEMPT/'qualification/run.json').read_text(encoding='utf-8'))
    assert prior['completed'] is False and prior['stop_reason'] == 'size monitor failed all three bounded attempts'
    assert prior['commands'][-1]['exit'] == 1 and prior['commands'][-1]['name'] == 'replay'
    output = (ATTEMPT/'qualification/replay.stdout.txt').read_text(encoding='utf-8')
    assert re.findall(r'replay stopped by stop file before block (\d+);',output) == ['6623297']
    assert 'replay matched:' not in output
    for name,digest in prior['input_sha256'].items():
        assert r.sha(ATTEMPT/'inputs'/name) == digest
    manifests = dict(prior['previous_manifest_sha256'],**{ATTEMPT.name:r.sha(ATTEMPT/'SHA256SUMS')})
    count = 0
    for name,digest in manifests.items():
        directory = HERE.parent/name
        assert r.sha(directory/'SHA256SUMS') == digest
        for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected,relative = line.split(None,1)
            assert r.sha(directory/relative) == expected,(name,relative)
            count += 1
    r.record.update(previous_manifest_sha256=manifests,previous_files_verified=count,imported_runner_sha256=r.sha(BASE/'run.py'))
    r.record['backup_before'] = r.metadata(backup,'backup-before')
    r.record['baseline_before'] = {h:r.metadata(p,'baseline-'+h+'-before') for h,p in r.BASELINES.items()}
    assert r.record['backup_before'] == prior['backup_after']
    assert r.record['baseline_before'] == prior['baseline_after']
    r.record['checkpoint_before_sha256'] = r.inventory(checkpoint)
    assert r.record['checkpoint_before_sha256'] == prior['recovery_checkpoint_sha256']
    r.record['target_before_cold_sha256'] = r.inventory(closed)
    r.record['selected_inventory'] = r.inventory(r.SELECTED)
    r.record['candidate_inventory'] = r.inventory(PRIOR_RUN/'node')
    assert r.record['selected_inventory'] == prior['selected_inventory']
    assert r.record['candidate_inventory'] == prior['candidate_inventory']
    assert r.sha(PRIOR_RUN/'bin/replay-tests') == prior['binary_sha256'] == REPLAY_SHA
    r.record['binary_sha256'] = REPLAY_SHA
    r.record['stop_sha256'] = r.sha(PRIOR_RUN/'STOP')
    assert r.sha(ATTEMPT/'qualification/STOP') == r.record['stop_sha256']
    shutil.copyfile(PRIOR_RUN/'STOP',RUN/'attempt-STOP')
    shutil.copyfile(PRIOR_RUN/'run.json',RUN/'attempt-final-run.json')
    identity = (closed/'replay-identity.json').read_bytes()
    assert identity == (checkpoint/'replay-identity.json').read_bytes()
    assert r.sha(closed/'replay-identity.json') == prior['checkpoint_identity_sha256']
    (RUN/'replay-identity.json').write_bytes(identity)
    r.record['checkpoint_identity_sha256'] = prior['checkpoint_identity_sha256']
    r.record['recovery_bundle'] = 'restart-ticket-encoder-replay-2400000-v2-2026-10-09'
    old = (ATTEMPT/'inputs/details_test.go').read_bytes()
    assert old.count(b'const height = uint64(6900000)') == 1
    assert (HERE/'details_test.go').read_bytes() == old.replace(b'const height = uint64(6900000)',b'const height = uint64(6623296)',1)
    env = r.environment(backup)
    env.pop('FUSION_RESTART_REPLAY_END')
    env.update(FUSION_RESTART_INSPECT_REPLAY_DIR=str(closed),FUSION_RESTART_INSPECT_REPLAY_HEIGHT='6623296')
    r.record['runtime_environment'] = {k:v for k,v in env.items() if k.startswith(('GO','FUSION_')) or k in ['CGO_ENABLED','TMPDIR']}
    r.record['toolchain'] = {'go_binary_sha256':r.sha(r.TOOLCHAIN/'bin/go'),'go_env':json.loads(subprocess.check_output(['go','env','-json'],cwd=PRIOR_RUN/'node',env=env,text=True))}
    assert r.record['toolchain']['go_binary_sha256'] == prior['toolchain']['go_binary_sha256']
    assert r.record['toolchain']['go_env']['GOVERSION'] == 'go1.27.1'
    overlay = {'Replace':{str(PRIOR_RUN/'node/tests/restart/details_test.go'):str(HERE/'details_test.go')}}
    (RUN/'observer-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n',encoding='utf-8')
    r.record['observer_overlay_sha256'] = r.sha(RUN/'observer-overlay.json')
    r.execute('observer-build',['timeout','--kill-after=20s','7m','go','test','-c','-p=2','-trimpath','-buildvcs=false','-overlay',str(RUN/'observer-overlay.json'),'-o',str(RUN/'bin/observer'),'./tests/restart'],PRIOR_RUN/'node',env)
    r.record['observer_binary_sha256'] = r.sha(RUN/'bin/observer')
    r.execute('observer-build-info',['go','version','-m',str(RUN/'bin/observer')],PRIOR_RUN/'node',env)
    for name,binary,test in [('reference',RUN/'bin/observer','TestCandidateReplayReference'),('cold-head',PRIOR_RUN/'bin/replay-tests','TestPreservedReplayHeadReadOnly'),('cold-details',RUN/'bin/observer','TestCandidateReplayColdDetails')]:
        r.execute(name,['timeout','--kill-after=10s','3m',str(binary),'-test.run=^'+test+'$','-test.v','-test.count=1','-test.timeout=2m'],PRIOR_RUN/'node/tests/restart',env)
    observations = {}
    for name in ['reference','cold-details']:
        matches = re.findall(r'candidate endpoint observation: (\{.*\})',(RUN/(name+'.stdout.txt')).read_text(encoding='utf-8'))
        assert len(matches) == 1
        observations[name] = json.loads(matches[0])
    cold = observations['cold-details'].copy()
    tickets = cold.pop('TicketCount')
    assert tickets > 0 and cold == observations['reference'] and cold['Number'] == 6623296
    r.record['endpoint_observations'] = observations
    r.record['inspect_passed'] = True


def finalize(backup,checkpoint,closed):
    r.record['backup_after'] = r.metadata(backup,'backup-after')
    r.record['baseline_after'] = {h:r.metadata(p,'baseline-'+h+'-after') for h,p in r.BASELINES.items()}
    checks = {
        'backup_metadata_unchanged':r.record['backup_after'] == r.record.get('backup_before'),
        'baseline_metadata_unchanged':r.record['baseline_after'] == r.record.get('baseline_before'),
        'checkpoint_bytes_unchanged':r.inventory(checkpoint) == r.record.get('checkpoint_before_sha256'),
        'target_bytes_unchanged':r.inventory(closed) == r.record.get('target_before_cold_sha256'),
        'selected_unchanged':r.inventory(r.SELECTED) == r.record.get('selected_inventory'),
        'candidate_unchanged':r.inventory(PRIOR_RUN/'node') == r.record.get('candidate_inventory'),
        'replay_binary_unchanged':r.sha(PRIOR_RUN/'bin/replay-tests') == REPLAY_SHA,
        'stop_unchanged':r.sha(PRIOR_RUN/'STOP') == r.record.get('stop_sha256'),
        'inputs_unchanged':r.inventory(HERE) == r.record['input_sha256'],
        'imported_runner_unchanged':r.sha(BASE/'run.py') == r.record.get('imported_runner_sha256'),
        'observer_unchanged':(RUN/'bin/observer').exists() and r.sha(RUN/'bin/observer') == r.record.get('observer_binary_sha256'),
        'overlay_unchanged':(RUN/'observer-overlay.json').exists() and r.sha(RUN/'observer-overlay.json') == r.record.get('observer_overlay_sha256')
    }
    r.record['preservation_checks'] = checks
    r.record['remaining_bytes'] = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    measured = subprocess.run(['timeout','--kill-after=2s','15s','du','-sB1',str(closed)],capture_output=True,text=True)
    r.record['closed_size_measurement'] = {'exit':measured.returncode,'stdout':measured.stdout,'stderr':measured.stderr}
    r.record['result_logical_bytes'] = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    r.record['completed'] = r.record['result_logical_bytes'] < 256*1024**2 and r.record.get('inspect_passed',False) and all(checks.values()) and not r.record.get('failures') and measured.returncode == 0
    r.record['finished'] = r.now()
    r.save()
    shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('bin','tmp'))
    print('inspection completed',r.record['completed'],flush=True)
    assert r.record['completed']


assert os.getuid() == 1000 and len(sys.argv) == 6
parent_net,parent_mount = sys.argv[1:3]
backup,checkpoint,closed = map(Path,sys.argv[3:])
assert parent_net != os.readlink('/proc/self/ns/net') and parent_mount != os.readlink('/proc/self/ns/mnt')
assert not RUN.exists() and not (HERE/'qualification').exists()
links = subprocess.check_output(['ip','-brief','link'],text=True)
assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
mounts = {name:r.mount_description(path) for name,path in [('backup_mount',backup),('checkpoint_mount',checkpoint),('closed_mount',closed)]}
capacity = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
assert capacity['/home/rehearsal/results'] > 21*1024**3 and capacity['/mnt/d'] > 51*1024**3
RUN.mkdir()
(RUN/'bin').mkdir()
(RUN/'tmp').mkdir()
processes = subprocess.check_output(['ps','-eo','pid,etimes,comm'],text=True)
(RUN/'processes-before.txt').write_text(processes,encoding='utf-8')
assert not re.search(r'^\s*\d+\s+\d+\s+(?:replay-tests|efsn|observer)(?:\s|$)',processes,re.M)
r.record = dict(mounts,starting_capacity_bytes=capacity,started=r.now(),uid=os.getuid(),namespace=os.readlink('/proc/self/ns/net'),mount_namespace=os.readlink('/proc/self/ns/mnt'),parent_namespace=parent_net,parent_mount_namespace=parent_mount,links=links,input_sha256=r.inventory(HERE),commands=[],requested_attempt_height=6900000,inspection_height=6623296)
r.save()
try:
    inspect(backup,checkpoint,closed)
except BaseException as exc:
    r.record.setdefault('failures',[]).append({'error':repr(exc),'time':r.now()})
    raise
finally:
    finalize(backup,checkpoint,closed)
