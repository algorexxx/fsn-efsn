from pathlib import Path
import datetime
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path('/home/rehearsal/results') / HERE.name
TARGET = Path('/home/rehearsal/replay/candidate-ticket-encoding-100000')
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node')
PRIOR = HERE.parent / 'restart-ticket-encoder-regressions-2026-10-08'
CANDIDATE = HERE.parent / 'restart-ticket-encoder-candidate-v2-2026-10-08'
TOOLCHAIN = Path('/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go')
STOP = RUN/'STOP'
TEST_FILES = ['replay_linux_test.go', 'replay_resume_linux_test.go', 'replay_inspection_linux_test.go']
BASELINES = {str(h): Path('/home/rehearsal/replay')/('baseline-mainnet-'+str(h)) for h in [3300000,3600000]}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    return {p.relative_to(directory).as_posix(): sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def metadata(directory, label):
    rows = []
    for path in sorted(directory.iterdir()):
        assert path.is_file() and not path.is_symlink(), str(path)
        stat = path.stat()
        rows.append([path.name, stat.st_size, stat.st_mtime_ns])
    raw = (json.dumps(rows,separators=(',',':'))+'\n').encode('utf-8')
    (RUN/(label+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
    return {'files':len(rows),'logical_bytes':sum(row[1] for row in rows),'metadata_sha256':hashlib.sha256(raw).hexdigest()}


def save():
    (RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')


def execute(name, argv, cwd, env):
    entry = {'name':name,'argv':argv,'cwd':str(cwd),'started':now()}
    with (RUN/(name+'.stdout.txt')).open('wb') as out, (RUN/(name+'.stderr.txt')).open('wb') as err:
        entry['exit'] = subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err).returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print(name,entry['exit'],flush=True)
    if entry['exit']:
        raise RuntimeError('command failed: '+name)


def environment(backup):
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('GO') or key.startswith('FUSION_') or key.startswith('F12_'):
            env.pop(key)
    env.update(PATH=str(TOOLCHAIN/'bin')+':/usr/bin:/bin',GOENV='off',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',CGO_ENABLED='1',GOAMD64='v1',GOMAXPROCS='2',GOCACHE='/home/rehearsal/results/restart-release-selection-2026-10-04/repeat-cache',GOMODCACHE='/home/rehearsal/go/pkg/mod',GOTMPDIR=str(RUN/'tmp'),TMPDIR=str(RUN/'tmp'),PYTHONDONTWRITEBYTECODE='1',FUSION_RESTART_CHAINDATA=str(backup),FUSION_RESTART_FULL_AUDIT='1',FUSION_RESTART_HOST_STORAGE='/mnt/d',FUSION_RESTART_REPLAY_END='100000')
    return env


def mount_description(path):
    mount = json.loads(subprocess.check_output(['findmnt','-J','-o','TARGET,SOURCE,OPTIONS','-T',str(path)],text=True))['filesystems'][0]
    assert mount['target'] == str(path) and 'ro' in mount['options'].split(',')
    return mount


def copy_tests(folder):
    testdir = folder/'tests/restart'
    testdir.mkdir(parents=True,exist_ok=True)
    assert not list(testdir.glob('*_test.go'))
    record['test_input_sha256'] = {}
    for name in TEST_FILES:
        source = REPO/'tests/restart'/name
        shutil.copyfile(source,testdir/name)
        record['test_input_sha256']['tests/restart/'+name] = sha(source)
    response = Path('docs/evidence/restart-2026-09-23/responses.json')
    (folder/response).parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(REPO/response,folder/response)
    record['test_input_sha256'][response.as_posix()] = sha(REPO/response)
    body = b'package restart\n\nimport (\n"encoding/json"\n"os"\n"testing"\n"github.com/FusionFoundation/efsn/v5/common"\n"github.com/FusionFoundation/efsn/v5/core/rawdb"\n"github.com/FusionFoundation/efsn/v5/core/types"\n"github.com/FusionFoundation/efsn/v5/ethdb"\n"github.com/FusionFoundation/efsn/v5/params"\n)\n\n'
    record['helper_extractions'] = []
    for filename,names in [('fixture_test.go',['rpcObservation','readRPCObservations','requireNoError']),('integrity_test.go',['inspectionBackup','openInspectionBackup'])]:
        source = REPO/'tests/restart'/filename
        raw = source.read_bytes()
        for name in names:
            start = re.search(rb'(?m)^(?:type|func) '+name.encode()+rb'[ (]',raw).start()
            end = start + re.search(rb'(?m)^}\r?\n',raw[start:]).end()
            chunk = raw[start:end]
            body += chunk+b'\n'
            record['helper_extractions'].append({'name':name,'source':'tests/restart/'+filename,'source_sha256':sha(source),'start_line':raw[:start].count(b'\n')+1,'end_line':raw[:end].count(b'\n'),'body_sha256':hashlib.sha256(chunk).hexdigest()})
    (RUN/'helpers_test.go').write_bytes(body)
    (testdir/'helpers_test.go').write_bytes(body)
    shutil.copyfile(HERE/'details_test.go',testdir/'details_test.go')
    record['test_input_sha256']['tests/restart/helpers_test.go'] = sha(RUN/'helpers_test.go')
    record['test_input_sha256']['tests/restart/details_test.go'] = sha(HERE/'details_test.go')


def allocated_size():
    for attempt in range(1,4):
        measured = subprocess.run(['timeout','--kill-after=2s','15s','du','-sB1',str(TARGET)],capture_output=True,text=True)
        fields = measured.stdout.split()
        valid = measured.returncode == 0 and len(fields) == 2 and fields[0].isdigit() and fields[1] == str(TARGET)
        record['size_measurements'].append({'time':now(),'attempt':attempt,'exit':measured.returncode,'stdout':measured.stdout,'stderr':measured.stderr})
        save()
        if valid:
            return int(fields[0])
        time.sleep(1)
    return None


def request_stop(reason):
    if not STOP.exists():
        STOP.write_text(reason+'\n',encoding='utf-8')
        record['stop_reason'] = reason
        save()
        print('clean stop requested:',reason,flush=True)


def run_replay(env):
    command = ['timeout','--kill-after=20s','1h',str(RUN/'bin/replay-tests'),'-test.run=^TestPreservedHistoryReplay$','-test.v','-test.count=1','-test.timeout=55m']
    env = dict(env,FUSION_RESTART_REPLAY_DIR=str(TARGET),FUSION_RESTART_REPLAY_STOP_FILE=str(STOP))
    entry = {'name':'replay','argv':command,'cwd':str(RUN/'node/tests/restart'),'started':now()}
    start = time.monotonic()
    next_measurement = start
    with (RUN/'replay.stdout.txt').open('wb') as out, (RUN/'replay.stderr.txt').open('wb') as err:
        process = subprocess.Popen(command,cwd=entry['cwd'],env=env,stdout=out,stderr=err)
        record['replay_pid'] = process.pid
        record['replay_started'] = entry['started']
        save()
        try:
            while process.poll() is None:
                if time.monotonic()-start >= 1800:
                    request_stop('30-minute initial range allowance reached')
                if time.monotonic() >= next_measurement and TARGET.exists():
                    size = allocated_size()
                    if size is None:
                        request_stop('size monitor failed all three bounded attempts')
                    elif size >= 4*1024**3:
                        request_stop('4 GiB sampled target allowance reached')
                    print('replay monitored:',size,'allocated bytes',flush=True)
                    next_measurement = time.monotonic()+30
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if process.poll() is None:
                request_stop('runner interrupted; retain partial target')
                process.wait()
        entry['exit'] = process.returncode
    entry['finished'] = now()
    record['commands'].append(entry)
    save()
    print('replay',entry['exit'],flush=True)
    if entry['exit'] or STOP.exists():
        raise RuntimeError('replay stopped or failed; no automatic continuation')
    record['replay_passed'] = True
    record['closed_allocated_bytes'] = allocated_size()
    assert record['closed_allocated_bytes'] is not None
    shutil.copyfile(TARGET/'replay-identity.json',RUN/'replay-identity.json')


def prepare_and_replay(backup, env):
    record['runtime_environment'] = {key:value for key,value in env.items() if key.startswith('FUSION_') or key in ['GOMAXPROCS','GOENV','GOFLAGS','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOWORK','GOCACHE','GOMODCACHE','GOTMPDIR','TMPDIR','CGO_ENABLED','GOAMD64']}
    prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
    previous = dict(prior['previous_manifest_sha256'],**{PRIOR.name:sha(PRIOR/'SHA256SUMS')})
    checked = 0
    for name,digest in previous.items():
        directory = HERE.parent/name
        assert sha(directory/'SHA256SUMS') == digest
        for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            expected,relative = line.split(None,1)
            assert sha(directory/relative) == expected,(name,relative)
            checked += 1
    record['previous_manifest_sha256'] = previous
    record['previous_files_verified'] = checked
    record['investigation_commit'] = subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
    assert record['investigation_commit'].startswith('aeb0a8c7')
    record['backup_before'] = metadata(backup,'backup-before')
    historical = json.loads((HERE.parent/'restart-ticket-compression-2026-10-08/qualification/run.json').read_text(encoding='utf-8'))
    assert record['backup_before'] == historical['backup_after']
    record['baseline_before'] = {name:metadata(path,'baseline-'+name+'-before') for name,path in BASELINES.items()}
    expected = json.loads((HERE.parent/'restart-release-jwt-2026-10-04/node-inventory.json').read_text(encoding='utf-8'))
    assert inventory(SELECTED) == expected
    record['selected_inventory'] = expected.copy()
    record['toolchain'] = {'go_binary_sha256':sha(TOOLCHAIN/'bin/go'),'go_env':json.loads(subprocess.check_output(['go','env','-json'],cwd=SELECTED,env=env,text=True))}
    assert record['toolchain']['go_binary_sha256'] == prior['toolchains']['modern']['go_binary_sha256']
    assert record['toolchain']['go_env']['GOVERSION'] == 'go1.27.1'
    shutil.copytree(SELECTED,RUN/'node')
    assert inventory(RUN/'node') == expected
    execute('patch-check',['git','apply','--check',str(CANDIDATE/'candidate.patch')],RUN/'node',env)
    execute('patch-apply',['git','apply',str(CANDIDATE/'candidate.patch')],RUN/'node',env)
    candidate = json.loads((CANDIDATE/'qualification/run.json').read_text(encoding='utf-8'))
    expected.update(candidate['runtime_input_sha256'])
    assert inventory(RUN/'node') == expected
    copy_tests(RUN/'node')
    expected.update(record['test_input_sha256'])
    assert inventory(RUN/'node') == expected
    record['candidate_inventory'] = expected
    execute('build',['timeout','--kill-after=20s','7m','go','test','-c','-p=2','-trimpath','-buildvcs=false','-o',str(RUN/'bin/replay-tests'),'./tests/restart'],RUN/'node',env)
    record['binary_sha256'] = sha(RUN/'bin/replay-tests')
    execute('build-info',['go','version','-m',str(RUN/'bin/replay-tests')],RUN/'node',env)
    execute('reference',['timeout','--kill-after=10s','3m',str(RUN/'bin/replay-tests'),'-test.run=^TestCandidateReplayReference$','-test.v','-test.count=1','-test.timeout=2m'],RUN/'node/tests/restart',env)
    save()
    run_replay(env)


def inspect(backup, closed, env):
    assert record['replay_passed'] and not STOP.exists()
    record['closed_mount'] = mount_description(closed)
    assert sha(RUN/'bin/replay-tests') == record['binary_sha256']
    record['target_before_cold_sha256'] = inventory(closed)
    env = dict(env,FUSION_RESTART_INSPECT_REPLAY_DIR=str(closed),FUSION_RESTART_INSPECT_REPLAY_HEIGHT='100000')
    for name,test in [('cold-head','TestPreservedReplayHeadReadOnly'),('cold-details','TestCandidateReplayColdDetails')]:
        execute(name,['timeout','--kill-after=10s','3m',str(RUN/'bin/replay-tests'),'-test.run=^'+test+'$','-test.v','-test.count=1','-test.timeout=2m'],RUN/'node/tests/restart',env)
    assert inventory(closed) == record['target_before_cold_sha256']
    record['cold_target_bytes_unchanged'] = True
    observations = {}
    for name in ['reference','cold-details']:
        output = (RUN/(name+'.stdout.txt')).read_text(encoding='utf-8')
        matches = re.findall(r'candidate endpoint observation: (\{.*\})',output)
        assert len(matches) == 1
        observations[name] = json.loads(matches[0])
    cold = observations['cold-details'].copy()
    count = cold.pop('TicketCount')
    assert count > 0 and cold == observations['reference']
    record['endpoint_observations'] = observations
    record['inspect_passed'] = True


def finalize(backup):
    record['backup_after'] = metadata(backup,'backup-after')
    record['baseline_after'] = {name:metadata(path,'baseline-'+name+'-after') for name,path in BASELINES.items()}
    record['backup_unchanged'] = record.get('backup_before') == record['backup_after']
    record['baselines_unchanged'] = record.get('baseline_before') == record['baseline_after']
    record['selected_unchanged'] = inventory(SELECTED) == record.get('selected_inventory')
    record['candidate_unchanged'] = inventory(RUN/'node') == record.get('candidate_inventory')
    record['inputs_unchanged'] = inventory(HERE) == record['input_sha256']
    record['remaining_bytes'] = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
    record['completed'] = all(record.get(name,False) for name in ['replay_passed','inspect_passed','cold_target_bytes_unchanged','backup_unchanged','baselines_unchanged','selected_unchanged','candidate_unchanged','inputs_unchanged']) and not record.get('failures')
    record['finished'] = now()
    save()
    assert not (HERE/'qualification').exists()
    shutil.copytree(RUN,HERE/'qualification',ignore=shutil.ignore_patterns('bin','tmp','node'))
    print('completed',record['completed'],flush=True)
    if not record['completed']:
        raise RuntimeError('qualification incomplete; evidence retained')


if __name__ == '__main__':
    assert os.getuid() == 1000 and len(sys.argv) in [5,6]
    phase,parent_net,parent_mount = sys.argv[1:4]
    backup = Path(sys.argv[4])
    assert parent_net != os.readlink('/proc/self/ns/net') and parent_mount != os.readlink('/proc/self/ns/mnt')
    mount = mount_description(backup)
    links = subprocess.check_output(['ip','-brief','link'],text=True)
    assert len(links.splitlines()) == 1 and links.startswith('lo ') and 'DOWN' in links
    if phase == 'replay':
        assert not RUN.exists() and not TARGET.exists() and not (HERE/'qualification').exists()
        capacity = {p:shutil.disk_usage(p).free for p in ['/home/rehearsal/results','/mnt/d']}
        assert capacity['/home/rehearsal/results'] > 30*1024**3 and capacity['/mnt/d'] > 60*1024**3
        subprocess.run([str(TOOLCHAIN/'bin/gofmt'),'-w',str(HERE/'details_test.go')],check=True)
        RUN.mkdir()
        (RUN/'bin').mkdir()
        (RUN/'tmp').mkdir()
        record = {'started':now(),'uid':os.getuid(),'namespace':os.readlink('/proc/self/ns/net'),'mount_namespace':os.readlink('/proc/self/ns/mnt'),'parent_namespace':parent_net,'parent_mount_namespace':parent_mount,'backup_mount':mount,'links':links,'target':str(TARGET),'capacity_bytes':capacity,'input_sha256':inventory(HERE),'commands':[],'size_measurements':[],'preservation_marker':Path('/home/rehearsal/results/backup-copy-2026-09-23/verified.txt').read_text(encoding='utf-8')}
        save()
    else:
        record = json.loads((RUN/'run.json').read_text(encoding='utf-8'))
    try:
        if phase == 'replay':
            prepare_and_replay(backup,environment(backup))
        elif phase == 'inspect':
            inspect(backup,Path(sys.argv[5]),environment(backup))
        elif phase == 'finalize':
            finalize(backup)
        else:
            raise ValueError(phase)
    except BaseException as exc:
        record.setdefault('failures',[]).append({'phase':phase,'error':repr(exc),'time':now()})
        raise
    finally:
        save()
