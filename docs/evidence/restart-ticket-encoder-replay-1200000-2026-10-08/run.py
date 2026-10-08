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
PRIOR = HERE.parent/'restart-ticket-encoder-replay-900000-2026-10-08'
BASE = HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08'
PRIOR_RUN = Path('/home/rehearsal/results')/PRIOR.name
RUN = Path('/home/rehearsal/results')/HERE.name
TARGET = Path('/home/rehearsal/replay/candidate-ticket-encoding-1200000')
REPLAY_SHA = 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'
module = importlib.util.spec_from_file_location('retained_replay_runner',BASE/'run.py')
r = importlib.util.module_from_spec(module)
module.loader.exec_module(r)
r.HERE,r.RUN,r.TARGET,r.STOP = HERE,RUN,TARGET,RUN/'STOP'


def run_test(name,binary,test,env):
    r.execute(name,['timeout','--kill-after=10s','3m',str(RUN/'bin'/binary),'-test.run=^'+test+'$','-test.v','-test.count=1','-test.timeout=2m'],RUN/'node/tests/restart',env)


def prepare(backup,checkpoint,env):
    prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
    assert prior['completed'] and prior['binary_sha256'] == REPLAY_SHA
    manifests = dict(prior['previous_manifest_sha256'],**{PRIOR.name:r.sha(PRIOR/'SHA256SUMS')})
    count = 0
    for name,digest in manifests.items():
        directory = HERE.parent/name
        assert r.sha(directory/'SHA256SUMS') == digest
        for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected,relative = line.split(None,1)
            assert r.sha(directory/relative) == expected,(name,relative)
            count += 1
    r.record['previous_manifest_sha256'] = manifests
    r.record['previous_files_verified'] = count
    r.record['imported_runner_sha256'] = r.sha(BASE/'run.py')
    r.record['investigation_commit'] = subprocess.check_output(['git','-C',str(r.REPO),'rev-parse','HEAD'],text=True).strip()
    assert r.record['investigation_commit'].startswith('cbed8717')
    r.record['backup_before'] = r.metadata(backup,'backup-before')
    assert r.record['backup_before'] == prior['backup_after']
    r.record['baseline_before'] = {name:r.metadata(path,'baseline-'+name+'-before') for name,path in r.BASELINES.items()}
    assert r.record['baseline_before'] == prior['baseline_after']
    r.record['checkpoint_before_sha256'] = r.inventory(checkpoint)
    assert r.record['checkpoint_before_sha256'] == prior['target_before_cold_sha256']
    assert r.inventory(r.SELECTED) == prior['selected_inventory']
    assert r.inventory(PRIOR_RUN/'node') == prior['candidate_inventory']
    r.record['selected_inventory'] = prior['selected_inventory']
    r.record['candidate_inventory'] = prior['candidate_inventory']
    r.record['toolchain'] = {'go_binary_sha256':r.sha(r.TOOLCHAIN/'bin/go'),'go_env':json.loads(subprocess.check_output(['go','env','-json'],cwd=r.SELECTED,env=env,text=True))}
    assert r.record['toolchain']['go_binary_sha256'] == prior['toolchain']['go_binary_sha256']
    assert r.record['toolchain']['go_env']['GOVERSION'] == 'go1.27.1'
    assert r.sha(PRIOR_RUN/'bin/replay-tests') == REPLAY_SHA
    shutil.copyfile(PRIOR_RUN/'bin/replay-tests',RUN/'bin/replay-tests')
    os.chmod(RUN/'bin/replay-tests',0o755)
    assert r.sha(RUN/'bin/replay-tests') == REPLAY_SHA
    r.record['binary_sha256'] = REPLAY_SHA
    shutil.copytree(PRIOR_RUN/'node',RUN/'node')
    assert r.inventory(RUN/'node') == prior['candidate_inventory']
    original = (PRIOR/'details_test.go').read_bytes()
    assert original.count(b'const height = uint64(900000)') == 1
    assert (HERE/'details_test.go').read_bytes() == original.replace(b'const height = uint64(900000)',b'const height = uint64(1200000)',1)
    overlay = {'Replace':{str(RUN/'node/tests/restart/details_test.go'):str(HERE/'details_test.go')}}
    (RUN/'observer-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n',encoding='utf-8')
    r.record['observer_overlay_sha256'] = r.sha(RUN/'observer-overlay.json')
    r.execute('observer-build',['timeout','--kill-after=20s','7m','go','test','-c','-p=2','-trimpath','-buildvcs=false','-overlay',str(RUN/'observer-overlay.json'),'-o',str(RUN/'bin/observer'),'./tests/restart'],RUN/'node',env)
    r.record['observer_binary_sha256'] = r.sha(RUN/'bin/observer')
    r.execute('observer-build-info',['go','version','-m',str(RUN/'bin/observer')],RUN/'node',env)
    check_env = dict(env,FUSION_RESTART_INSPECT_REPLAY_DIR=str(checkpoint),FUSION_RESTART_INSPECT_REPLAY_HEIGHT='900000')
    run_test('checkpoint-cold-head','replay-tests','TestPreservedReplayHeadReadOnly',check_env)
    assert r.inventory(checkpoint) == r.record['checkpoint_before_sha256']
    run_test('reference','observer','TestCandidateReplayReference',env)
    r.record['copy_started'] = r.now()
    shutil.copytree(checkpoint,TARGET)
    assert r.inventory(TARGET) == r.record['checkpoint_before_sha256']
    assert r.inventory(checkpoint) == r.record['checkpoint_before_sha256']
    r.record['copy_finished'] = r.now()
    r.record['copy_verified'] = True
    r.record['checkpoint_identity_sha256'] = r.sha(checkpoint/'replay-identity.json')
    assert r.sha(TARGET/'replay-identity.json') == r.record['checkpoint_identity_sha256']
    r.save()
    r.run_replay(env)
    assert r.sha(TARGET/'replay-identity.json') == r.record['checkpoint_identity_sha256']


def inspect(closed,env):
    assert r.record['replay_passed'] and not r.STOP.exists()
    assert r.sha(RUN/'bin/replay-tests') == REPLAY_SHA
    assert r.sha(RUN/'bin/observer') == r.record['observer_binary_sha256']
    r.record['closed_mount'] = r.mount_description(closed)
    r.record['target_before_cold_sha256'] = r.inventory(closed)
    env = dict(env,FUSION_RESTART_INSPECT_REPLAY_DIR=str(closed),FUSION_RESTART_INSPECT_REPLAY_HEIGHT='1200000')
    run_test('cold-head','replay-tests','TestPreservedReplayHeadReadOnly',env)
    run_test('cold-details','observer','TestCandidateReplayColdDetails',env)
    assert r.inventory(closed) == r.record['target_before_cold_sha256']
    r.record['cold_target_bytes_unchanged'] = True
    observations = {}
    for name in ['reference','cold-details']:
        matches = re.findall(r'candidate endpoint observation: (\{.*\})',(RUN/(name+'.stdout.txt')).read_text(encoding='utf-8'))
        assert len(matches) == 1
        observations[name] = json.loads(matches[0])
    cold = observations['cold-details'].copy()
    tickets = cold.pop('TicketCount')
    assert tickets > 0 and cold == observations['reference'] and cold['Number'] == 1200000
    r.record['endpoint_observations'] = observations
    r.record['inspect_passed'] = True


def finalize(backup,checkpoint):
    checks = {
        'checkpoint_bytes_unchanged':r.inventory(checkpoint) == r.record.get('checkpoint_before_sha256'),
        'prior_candidate_source_unchanged':r.inventory(PRIOR_RUN/'node') == r.record.get('candidate_inventory'),
        'prior_replay_binary_unchanged':r.sha(PRIOR_RUN/'bin/replay-tests') == REPLAY_SHA,
        'replay_binary_unchanged':(RUN/'bin/replay-tests').exists() and r.sha(RUN/'bin/replay-tests') == REPLAY_SHA,
        'observer_binary_unchanged':(RUN/'bin/observer').exists() and r.sha(RUN/'bin/observer') == r.record.get('observer_binary_sha256'),
        'observer_overlay_unchanged':(RUN/'observer-overlay.json').exists() and r.sha(RUN/'observer-overlay.json') == r.record.get('observer_overlay_sha256'),
        'imported_runner_unchanged':r.sha(BASE/'run.py') == r.record.get('imported_runner_sha256')
    }
    r.record['additional_preservation_checks'] = checks
    if not all(checks.values()):
        r.record.setdefault('failures',[]).append({'phase':'finalize','error':'additional preservation check failed','checks':checks})
    r.finalize(backup)


if __name__ == '__main__':
    assert os.getuid() == 1000 and len(sys.argv) in [6,7]
    phase,parent_net,parent_mount = sys.argv[1:4]
    backup,checkpoint = map(Path,sys.argv[4:6])
    assert parent_net != os.readlink('/proc/self/ns/net') and parent_mount != os.readlink('/proc/self/ns/mnt')
    mounts = {'backup_mount':r.mount_description(backup),'checkpoint_mount':r.mount_description(checkpoint)}
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    if phase == 'replay':
        assert not RUN.exists() and not TARGET.exists() and not (HERE/'qualification').exists()
        capacity = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
        assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
        RUN.mkdir()
        (RUN/'bin').mkdir()
        (RUN/'tmp').mkdir()
        r.record = dict(mounts,started=r.now(),uid=os.getuid(),namespace=os.readlink('/proc/self/ns/net'),mount_namespace=os.readlink('/proc/self/ns/mnt'),parent_namespace=parent_net,parent_mount_namespace=parent_mount,links=links,target=str(TARGET),capacity_bytes=capacity,input_sha256=r.inventory(HERE),commands=[],size_measurements=[],preservation_marker=Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').read_text(encoding='utf-8'))
        r.save()
    else:
        r.record = json.loads((RUN/'run.json').read_text(encoding='utf-8'))
    env = dict(r.environment(backup),FUSION_RESTART_REPLAY_END='1200000',FUSION_RESTART_REPLAY_RESUME='1')
    try:
        if phase == 'replay':
            r.record['runtime_environment'] = {k:v for k,v in env.items() if k.startswith('FUSION_') or k in ['GOMAXPROCS','GOENV','GOFLAGS','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOWORK','GOCACHE','GOMODCACHE','GOTMPDIR','TMPDIR','CGO_ENABLED','GOAMD64']}
            prepare(backup,checkpoint,env)
        elif phase == 'inspect':
            inspect(Path(sys.argv[6]),env)
        elif phase == 'finalize':
            finalize(backup,checkpoint)
        else:
            raise ValueError(phase)
    except BaseException as exc:
        r.record.setdefault('failures',[]).append({'phase':phase,'error':repr(exc),'time':r.now()})
        raise
    finally:
        r.save()
