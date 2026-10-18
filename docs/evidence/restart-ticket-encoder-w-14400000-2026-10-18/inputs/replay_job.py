from pathlib import Path
import importlib.util
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import replay_monitor as monitor

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
REPO = HERE.parents[3]
CONFIG = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
monitor.validate_configuration(CONFIG)
assert BUNDLE.name == CONFIG['job']
PRIOR = REPO/'docs/evidence'/CONFIG['prior_bundle']
RECOVERY = REPO/'docs/evidence'/CONFIG['recovery_bundle']
BASE = REPO/'docs/evidence/restart-ticket-encoder-replay-100000-2026-10-08'
PRIOR_RUN = Path('/home/rehearsal/results')/CONFIG.get('stopped_attempt',CONFIG['prior_bundle'])
RUN = Path('/home/rehearsal/results')/CONFIG['job']
TARGET = Path('/home/rehearsal/replay')/CONFIG['target']
START,END = CONFIG['start_height'],CONFIG['end_height']
REPLAY_SHA = 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'
module = importlib.util.spec_from_file_location('retained_replay_runner',BASE/'run.py')
r = importlib.util.module_from_spec(module)
module.loader.exec_module(r)
r.HERE,r.RUN,r.TARGET,r.STOP = HERE,RUN,TARGET,RUN/'STOP'


def run_test(name,binary,test,env):
    r.execute(name,['timeout','--kill-after=10s','3m',str(RUN/'bin'/binary),'-test.run=^'+test+'$','-test.v','-test.count=1','-test.timeout=2m'],RUN/'node/tests/restart',env)


def prepare(backup,checkpoint,env):
    prior_inputs = PRIOR/'inputs' if (PRIOR/'inputs').is_dir() else PRIOR
    monitor.require_observer_change(CONFIG,prior_inputs,HERE)
    prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
    assert prior['completed'] and prior['inspect_passed'] and prior['binary_sha256'] == REPLAY_SHA
    if 'stopped_attempt' in CONFIG:
        failed = REPO/'docs/evidence'/CONFIG['stopped_attempt']
        monitor.require_verified_stopped(CONFIG,prior,json.loads((PRIOR/'verification.json').read_text(encoding='utf-8')),json.loads((failed/'completion.json').read_text(encoding='utf-8')))
        assert CONFIG['stopped_attempt'] in prior['previous_manifest_sha256']
        if prior.get('stop_kind') == 'host-reserve':
            assert not (PRIOR_RUN/'STOP').exists() and not (failed/'qualification/STOP').exists()
            evidence = {name:r.sha(failed/name) for name in ['completion.json','qualification/replay.stdout.txt','qualification/run.json']}
            assert evidence == prior['stop_evidence_sha256']
            r.record['prior_stop_evidence_sha256'] = evidence
            (RUN/'prior-stop-evidence.json').write_bytes((json.dumps(evidence,indent=2)+'\n').encode('utf-8'))
        else:
            assert r.sha(PRIOR_RUN/'STOP') == r.sha(failed/'qualification/STOP') == prior['stop_sha256']
            (RUN/'prior-STOP').write_bytes((PRIOR_RUN/'STOP').read_bytes())
            r.record['prior_stop_sha256'] = prior['stop_sha256']
    else:
        assert all(prior['additional_preservation_checks'].values()) and not prior.get('failures')
    if 'stopped_attempt' not in CONFIG and (PRIOR/'inputs').is_dir():
        qualified_manifests = monitor.require_completed_prior(CONFIG,PRIOR)
    assert not r.STOP.exists()
    manifests = dict(prior['previous_manifest_sha256'],**{PRIOR.name:r.sha(PRIOR/'SHA256SUMS')})
    if 'storage' in CONFIG:
        storage = CONFIG['storage']
        manifests[storage['migration_bundle']] = storage['migration_sha256']
        migrated = json.loads((BUNDLE.parent/storage['migration_bundle']/'verification.json').read_text(encoding='utf-8'))
        assert migrated['pass'] and migrated['endpoint']['Number'] <= START
        if migrated['endpoint']['Number'] == START:
            assert migrated['endpoint'] == prior['endpoint_observations']['cold-details']
        else:
            assert prior['configuration']['storage'] == storage
            assert prior['previous_manifest_sha256'][storage['migration_bundle']] == storage['migration_sha256']
    if 'prior_verification_bundle' in CONFIG:
        manifests.update(qualified_manifests)
    count = 0
    for name,digest in manifests.items():
        directory = BUNDLE.parent/name
        assert r.sha(directory/'SHA256SUMS') == digest
        for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected,relative = line.split(None,1)
            assert r.sha(directory/relative) == expected,(name,relative)
            count += 1
    r.record['previous_manifest_sha256'] = manifests
    r.record['previous_files_verified'] = count
    r.record['imported_runner_sha256'] = r.sha(BASE/'run.py')
    r.record['investigation_commit'] = subprocess.check_output(['git','-C',str(r.REPO),'rev-parse','HEAD'],text=True).strip()
    r.record['configuration'] = CONFIG
    r.record['replay_limits'] = CONFIG['limits']
    recovery = json.loads((RECOVERY/'qualification/run.json').read_text(encoding='utf-8'))
    r.record['recovery_checkpoint_sha256'] = r.inventory(RECOVERY_VIEW)
    assert r.record['recovery_checkpoint_sha256'] == recovery['target_before_cold_sha256']
    assert RECOVERY.name in manifests
    r.record['runner_snapshot_sha256'] = {name:r.sha(HERE/name) for name in ['replay_job.py','replay_monitor.py','replay_launch.py','replay_verify.py']}
    if 'storage' in CONFIG:
        import replay_image
        r.record['runner_snapshot_sha256']['replay_image.py'] = r.sha(HERE/'replay_image.py')
        r.record['local_fallback_before'] = r.metadata(replay_image.FALLBACK,'local-fallback-before')
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
    overlay = {'Replace':{str(RUN/'node/tests/restart/details_test.go'):str(HERE/'details_test.go')}}
    (RUN/'observer-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n',encoding='utf-8')
    r.record['observer_overlay_sha256'] = r.sha(RUN/'observer-overlay.json')
    r.execute('observer-build',['timeout','--kill-after=20s','7m','go','test','-c','-p=2','-trimpath','-buildvcs=false','-overlay',str(RUN/'observer-overlay.json'),'-o',str(RUN/'bin/observer'),'./tests/restart'],RUN/'node',env)
    r.record['observer_binary_sha256'] = r.sha(RUN/'bin/observer')
    r.execute('observer-build-info',['go','version','-m',str(RUN/'bin/observer')],RUN/'node',env)
    check_env = dict(env,FUSION_RESTART_INSPECT_REPLAY_DIR=str(checkpoint),FUSION_RESTART_INSPECT_REPLAY_HEIGHT=str(START))
    run_test('checkpoint-cold-head','replay-tests','TestPreservedReplayHeadReadOnly',check_env)
    assert r.inventory(checkpoint) == r.record['checkpoint_before_sha256']
    run_test('reference','observer','TestCandidateReplayReference',env)
    r.record['copy_started'] = r.now()
    if CONFIG['mode'] == 'copy':
        shutil.copytree(checkpoint,TARGET)
        assert r.inventory(TARGET) == r.record['checkpoint_before_sha256']
        assert r.inventory(checkpoint) == r.record['checkpoint_before_sha256']
    else:
        assert os.path.samefile(TARGET, checkpoint)
    r.record['copy_finished'] = r.now()
    r.record['copy_verified'] = CONFIG['mode'] == 'copy'
    r.record['resume_verified'] = True
    r.record['checkpoint_identity_sha256'] = r.sha(checkpoint/'replay-identity.json')
    assert r.sha(TARGET/'replay-identity.json') == r.record['checkpoint_identity_sha256']
    r.save()
    fcntl.flock(target_lock,fcntl.LOCK_UN)
    target_lock.close()
    monitor.run_replay(r,env,CONFIG['limits'])
    assert r.sha(TARGET/'replay-identity.json') == r.record['checkpoint_identity_sha256']


def inspect(closed,env):
    assert r.record['replay_passed'] and not r.STOP.exists()
    assert r.sha(RUN/'bin/replay-tests') == REPLAY_SHA
    assert r.sha(RUN/'bin/observer') == r.record['observer_binary_sha256']
    r.record['closed_mount'] = r.mount_description(closed)
    r.record['target_before_cold_sha256'] = r.inventory(closed)
    env = dict(env,FUSION_RESTART_INSPECT_REPLAY_DIR=str(closed),FUSION_RESTART_INSPECT_REPLAY_HEIGHT=str(END))
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
    assert tickets > 0 and cold == observations['reference'] and cold['Number'] == END
    r.record['endpoint_observations'] = observations
    r.record['inspect_passed'] = True


def finalize(backup,checkpoint):
    r.record['backup_after'] = r.metadata(backup,'backup-after')
    r.record['baseline_after'] = {name:r.metadata(path,'baseline-'+name+'-after') for name,path in r.BASELINES.items()}
    checks = {
        'recovery_checkpoint_unchanged':r.inventory(RECOVERY_VIEW) == r.record.get('recovery_checkpoint_sha256'),
        'checkpoint_preserved_or_validated_resume':r.inventory(checkpoint) == r.record.get('checkpoint_before_sha256') if CONFIG['mode'] == 'copy' else r.record.get('resume_verified',False),
        'prior_candidate_source_unchanged':r.inventory(PRIOR_RUN/'node') == r.record.get('candidate_inventory'),
        'prior_replay_binary_unchanged':r.sha(PRIOR_RUN/'bin/replay-tests') == REPLAY_SHA,
        'replay_binary_unchanged':(RUN/'bin/replay-tests').exists() and r.sha(RUN/'bin/replay-tests') == REPLAY_SHA,
        'observer_binary_unchanged':(RUN/'bin/observer').exists() and r.sha(RUN/'bin/observer') == r.record.get('observer_binary_sha256'),
        'observer_overlay_unchanged':(RUN/'observer-overlay.json').exists() and r.sha(RUN/'observer-overlay.json') == r.record.get('observer_overlay_sha256'),
        'imported_runner_unchanged':r.sha(BASE/'run.py') == r.record.get('imported_runner_sha256'),
        'runner_snapshot_unchanged':all(r.sha(HERE/name) == digest for name,digest in r.record.get('runner_snapshot_sha256',{}).items()) and bool(r.record.get('runner_snapshot_sha256'))
    }
    if 'stopped_attempt' in CONFIG:
        if 'prior_stop_evidence_sha256' in r.record:
            failed = REPO/'docs/evidence'/CONFIG['stopped_attempt']
            evidence = {name:r.sha(failed/name) for name in ['completion.json','qualification/replay.stdout.txt','qualification/run.json']}
            checks['prior_stop_unchanged'] = not (PRIOR_RUN/'STOP').exists() and not (failed/'qualification/STOP').exists() and evidence == r.record['prior_stop_evidence_sha256'] == json.loads((RUN/'prior-stop-evidence.json').read_bytes())
        else:
            checks['prior_stop_unchanged'] = r.sha(PRIOR_RUN/'STOP') == r.sha(RUN/'prior-STOP') == r.record.get('prior_stop_sha256')
    if 'storage' in CONFIG:
        import replay_image
        r.record['local_fallback_after'] = r.metadata(replay_image.FALLBACK,'local-fallback-after')
        checks['local_fallback_metadata_unchanged'] = r.record['local_fallback_before'] == r.record['local_fallback_after']
    r.record['additional_preservation_checks'] = checks
    r.record['backup_unchanged'] = r.record.get('backup_before') == r.record['backup_after']
    r.record['baselines_unchanged'] = r.record.get('baseline_before') == r.record['baseline_after']
    r.record['selected_unchanged'] = r.inventory(r.SELECTED) == r.record.get('selected_inventory')
    r.record['candidate_unchanged'] = r.inventory(RUN/'node') == r.record.get('candidate_inventory')
    r.record['inputs_unchanged'] = r.inventory(HERE) == r.record['input_sha256']
    r.record['remaining_bytes'] = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    if 'storage' in CONFIG:
        r.record['remaining_bytes'] = replay_image.sample_storage(CONFIG,r.record['storage_mount'])
    r.record['completed'] = all(r.record.get(name,False) for name in ['replay_passed','inspect_passed','cold_target_bytes_unchanged','backup_unchanged','baselines_unchanged','selected_unchanged','candidate_unchanged','inputs_unchanged']) and all(checks.values()) and not r.record.get('failures')
    r.record['finished'] = r.now()
    r.save()
    assert not (BUNDLE/'qualification').exists()
    shutil.copytree(RUN,BUNDLE/'qualification',ignore=shutil.ignore_patterns('bin','tmp','node'))
    print('completed',r.record['completed'],flush=True)
    if not r.record['completed']:
        raise RuntimeError('qualification incomplete; evidence retained')


def save_status():
    monitor.write_atomic(RUN/'run.json',json.dumps(r.record,indent=2)+'\n')
    log = RUN/'replay.stdout.txt'
    heights = re.findall(r'(?:replay progress: height=|replay matched: height=|replay starting at height=)(\d+)',log.read_text(encoding='utf-8') if log.exists() else '')
    status = {'phase':r.record.get('phase'),'started':r.record.get('started'),'updated':r.now(),'observed_height':int(heights[-1]) if heights else START,'observed_height_is_provisional':not r.record.get('completed',False),'target_height':END,'completed':r.record.get('completed',False),'stop_reason':r.record.get('stop_reason'),'failures':r.record.get('failures',[]),'replay_pid':r.record.get('replay_pid')}
    monitor.write_atomic(RUN/'status.json',json.dumps(status,indent=2)+'\n')


if __name__ == '__main__':
    assert os.getuid() == 1000 and len(sys.argv) in [7,8]
    phase,parent_net,parent_mount = sys.argv[1:4]
    backup,checkpoint,RECOVERY_VIEW = map(Path,sys.argv[4:7])
    assert parent_net != os.readlink('/proc/self/ns/net') and parent_mount != os.readlink('/proc/self/ns/mnt')
    mounts = {'backup_mount':r.mount_description(backup),'checkpoint_mount':r.mount_description(checkpoint),'recovery_mount':r.mount_description(RECOVERY_VIEW)}
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    r.save = save_status
    target_lock = (TARGET/'LOCK' if TARGET.exists() else checkpoint/'LOCK').open('rb')
    fcntl.flock(target_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    if phase == 'replay':
        assert not RUN.exists() and not (BUNDLE/'qualification').exists()
        assert TARGET.exists() == (CONFIG['mode'] == 'resume')
        capacity = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
        if 'storage' in CONFIG:
            import replay_image
            mounted = json.loads((BUNDLE/'storage-mounted.json').read_text(encoding='utf-8'))
            capacity = replay_image.sample_storage(CONFIG,mounted)
        existing_bytes = 0
        if CONFIG['mode'] == 'resume':
            fields = subprocess.check_output(['timeout','--kill-after=2s','15s','du','-sB1',str(TARGET)],text=True).split()
            assert len(fields) == 2 and fields[0].isdigit() and fields[1] == str(TARGET)
            existing_bytes = int(fields[0])
        required_capacity = monitor.require_starting_capacity(CONFIG,capacity,existing_bytes)
        RUN.mkdir()
        (RUN/'bin').mkdir()
        (RUN/'tmp').mkdir()
        r.record = dict(mounts,started=r.now(),uid=os.getuid(),namespace=os.readlink('/proc/self/ns/net'),mount_namespace=os.readlink('/proc/self/ns/mnt'),parent_namespace=parent_net,parent_mount_namespace=parent_mount,links=links,target=str(TARGET),capacity_bytes=capacity,input_sha256=r.inventory(HERE),commands=[],size_measurements=[],preservation_marker=Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').read_text(encoding='utf-8'))
        r.record.update(existing_allocated_bytes=existing_bytes,required_capacity_bytes=required_capacity)
        if 'storage' in CONFIG:
            r.record['storage_mount'] = mounted
        r.save()
    else:
        r.record = json.loads((RUN/'run.json').read_text(encoding='utf-8'))
    r.record['phase'] = phase
    env = dict(r.environment(backup),FUSION_RESTART_REPLAY_END=str(END),FUSION_RESTART_REPLAY_RESUME='1')
    try:
        if phase == 'replay':
            r.record['runtime_environment'] = {k:v for k,v in env.items() if k.startswith('FUSION_') or k in ['GOMAXPROCS','GOENV','GOFLAGS','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOWORK','GOCACHE','GOMODCACHE','GOTMPDIR','TMPDIR','CGO_ENABLED','GOAMD64']}
            prepare(backup,checkpoint,env)
        elif phase == 'inspect':
            inspect(Path(sys.argv[7]),env)
        elif phase == 'finalize':
            finalize(backup,checkpoint)
        else:
            raise ValueError(phase)
    except BaseException as exc:
        r.record.setdefault('failures',[]).append({'phase':phase,'error':repr(exc),'time':r.now()})
        raise
    finally:
        target_lock.close()
        r.save()
