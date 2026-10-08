from pathlib import Path
import difflib
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
Q = HERE/'qualification'
PRIOR = HERE.parent/'restart-ticket-encoder-replay-600000-2026-10-08'
BASE = HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08'
r = json.loads((Q/'run.json').read_text(encoding='utf-8'))
prior = json.loads((PRIOR/'qualification/run.json').read_text(encoding='utf-8'))
REPLAY_SHA = 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert r['completed'] and not r.get('failures') and not r.get('stop_reason')
for name in ['replay_passed','inspect_passed','cold_target_bytes_unchanged','backup_unchanged','baselines_unchanged','selected_unchanged','candidate_unchanged','inputs_unchanged','copy_verified']:
    assert r[name],name
assert all(r['additional_preservation_checks'].values()) and len(r['additional_preservation_checks']) == 7
assert r['uid'] == 1000 and r['namespace'] != r['parent_namespace'] and r['mount_namespace'] != r['parent_mount_namespace']
assert len(r['links'].splitlines()) == 1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
for name in ['backup_mount','checkpoint_mount','closed_mount']:
    assert 'ro' in r[name]['options'].split(',')
assert r['target'] == '/home/rehearsal/replay/candidate-ticket-encoding-900000'
for name,digest in r['input_sha256'].items():
    assert sha(HERE/name) == digest,name
previous_files = 0
for name,digest in r['previous_manifest_sha256'].items():
    directory = HERE.parent/name
    assert sha(directory/'SHA256SUMS') == digest
    for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,relative = line.split(None,1)
        assert sha(directory/relative) == expected,(name,relative)
        previous_files += 1
assert previous_files == r['previous_files_verified']
assert r['imported_runner_sha256'] == sha(BASE/'run.py')
assert r['selected_inventory'] == prior['selected_inventory']
assert r['candidate_inventory'] == prior['candidate_inventory']
assert r['binary_sha256'] == prior['binary_sha256'] == REPLAY_SHA
assert r['observer_binary_sha256'] != REPLAY_SHA
assert r['toolchain']['go_binary_sha256'] == prior['toolchain']['go_binary_sha256']
env = r['toolchain']['go_env']
assert env['GOVERSION'] == 'go1.27.1' and env['GOENV'] == '' and env['GOFLAGS'] == '-mod=readonly'
assert env['GOPROXY'] == env['GOSUMDB'] == 'off' and env['GOTOOLCHAIN'] == 'local'
assert env['GOOS'] == 'linux' and env['GOARCH'] == 'amd64' and env['GOAMD64'] == 'v1'
runtime = r['runtime_environment']
assert runtime['GOMAXPROCS'] == '2'
assert runtime['FUSION_RESTART_REPLAY_END'] == '900000' and runtime['FUSION_RESTART_REPLAY_RESUME'] == '1'
assert runtime['FUSION_RESTART_FULL_AUDIT'] == '1' and runtime['FUSION_RESTART_HOST_STORAGE'] == '/mnt/d'
old = (PRIOR/'details_test.go').read_bytes()
assert old.count(b'const height = uint64(600000)') == 1
new = old.replace(b'const height = uint64(600000)',b'const height = uint64(900000)',1)
assert (HERE/'details_test.go').read_bytes() == new
patch = ''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/details_test.go',tofile='b/details_test.go'))
assert (HERE/'observer-change.patch').read_text(encoding='utf-8') == patch
assert sha(Q/'observer-overlay.json') == r['observer_overlay_sha256']
overlay = json.loads((Q/'observer-overlay.json').read_text(encoding='utf-8'))
source = '/home/rehearsal/results/'+HERE.name+'/node/tests/restart/details_test.go'
destination = '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/'+HERE.name+'/details_test.go'
assert overlay == {'Replace':{source:destination}}
assert r['checkpoint_before_sha256'] == prior['target_before_cold_sha256'] and len(r['checkpoint_before_sha256']) == 297
identity_bytes = (Q/'replay-identity.json').read_bytes()
assert identity_bytes == (PRIOR/'qualification/replay-identity.json').read_bytes()
assert hashlib.sha256(identity_bytes).hexdigest() == r['checkpoint_identity_sha256']
identity = json.loads(identity_bytes)
assert identity['Format'] == 1 and identity['ExecutableHash'] == REPLAY_SHA
assert r['target_before_cold_sha256']['replay-identity.json'] == r['checkpoint_identity_sha256']
commands = r['commands']
assert [c['name'] for c in commands] == ['observer-build','observer-build-info','checkpoint-cold-head','reference','replay','cold-head','cold-details']
for c in commands:
    assert c['exit'] == 0 and c['started'] <= c['finished']
    assert not (Q/(c['name']+'.stderr.txt')).read_bytes()
assert commands[2]['finished'] <= commands[3]['started'] <= commands[3]['finished'] <= r['copy_started'] <= r['copy_finished'] <= commands[4]['started']
assert commands[4]['finished'] <= commands[5]['started'] <= commands[6]['started']
for name,test,binary in [('checkpoint-cold-head','TestPreservedReplayHeadReadOnly','replay-tests'),('reference','TestCandidateReplayReference','observer'),('replay','TestPreservedHistoryReplay','replay-tests'),('cold-head','TestPreservedReplayHeadReadOnly','replay-tests'),('cold-details','TestCandidateReplayColdDetails','observer')]:
    c = next(c for c in commands if c['name'] == name)
    assert any(arg.endswith('/bin/'+binary) for arg in c['argv'])
    output = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert output.endswith('PASS\n') and '--- FAIL:' not in output and '--- SKIP:' not in output
    assert re.findall(r'^--- PASS: (\S+) \(',output,re.M) == [test]
reference = r['endpoint_observations']['reference']
cold = r['endpoint_observations']['cold-details'].copy()
count = cold.pop('TicketCount')
assert count > 0 and cold == reference and reference['Number'] == 900000
assert reference['Transactions'] == reference['Receipts']
for name,observed in [('reference',reference),('cold-details',r['endpoint_observations']['cold-details'])]:
    output = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert json.loads(re.search(r'candidate endpoint observation: (\{.*\})',output)[1]) == observed
previous_endpoint = prior['endpoint_observations']['reference']
checkpoint = (Q/'checkpoint-cold-head.stdout.txt').read_text(encoding='utf-8')
assert 'closed replay matched: height=600000 hash='+previous_endpoint['Hash'] in checkpoint
output = (Q/'replay.stdout.txt').read_text(encoding='utf-8')
assert 'legacyCheckpointRangeEnd=2680000' in output
assert 'read-only resume preflight matched height=600000 hash='+previous_endpoint['Hash'] in output
assert 'replay starting at height=600000 hash='+previous_endpoint['Hash']+' resume=true' in output
match = re.search(r'replay matched: height=(\d+) hash=(0x[0-9a-f]+) root=(0x[0-9a-f]+) ticketCommitment=(0x[0-9a-f]+) tickets=(\d+)',output)
assert match and int(match[1]) == 900000 and match[2] == reference['Hash'] and match[3] == reference['Root'] and match[4] == reference['TicketCommitment'] and int(match[5]) == count
cold_log = (Q/'cold-head.stdout.txt').read_text(encoding='utf-8')
assert 'closed replay matched: height=900000 hash='+reference['Hash']+' root='+reference['Root']+' ticketCommitment='+reference['TicketCommitment'] in cold_log
for label,observed in [('backup-before',r['backup_before']),('backup-after',r['backup_after'])]+[('baseline-'+height+'-'+phase,r['baseline_'+phase][height]) for phase in ['before','after'] for height in ['3300000','3600000']]:
    raw = gzip.decompress((Q/(label+'.json.gz')).read_bytes())
    rows = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == observed['metadata_sha256']
    assert len(rows) == observed['files'] and sum(row[1] for row in rows) == observed['logical_bytes']
assert r['backup_before'] == r['backup_after'] == prior['backup_after']
assert r['baseline_before'] == r['baseline_after'] == prior['baseline_after']
assert r['closed_allocated_bytes'] < 4*1024**3
assert r['capacity_bytes']['/home/rehearsal/results'] > 30*1024**3 and r['capacity_bytes']['/mnt/d'] > 60*1024**3
assert r['remaining_bytes']['/home/rehearsal/results'] > 20*1024**3 and r['remaining_bytes']['/mnt/d'] > 50*1024**3
next_attempt = 1
monitor_retries = 0
for measurement in r['size_measurements']:
    assert measurement['attempt'] == next_attempt
    fields = measurement['stdout'].split()
    valid = measurement['exit'] == 0 and len(fields) == 2 and fields[0].isdigit() and fields[1] == r['target']
    if valid:
        next_attempt = 1
    else:
        monitor_retries += 1
        next_attempt += 1
        assert next_attempt <= 3
assert next_attempt == 1
result = {'pass':True,'commands':len(commands),'previous_files_verified':previous_files,'started':r['started'],'replay_started':commands[4]['started'],'replay_finished':commands[4]['finished'],'finished':r['finished'],'start_height':600000,'end_height':900000,'endpoint':dict(reference,TicketCount=count),'replay_binary_sha256':REPLAY_SHA,'observer_binary_sha256':r['observer_binary_sha256'],'checkpoint_files_verified':len(r['checkpoint_before_sha256']),'target_files_hashed':len(r['target_before_cold_sha256']),'closed_allocated_bytes':r['closed_allocated_bytes'],'remaining_bytes':r['remaining_bytes'],'legacy_checkpoint_end':2680000,'monitor_retries':monitor_retries}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='endpoint'},indent=2))
print(json.dumps({k:v for k,v in result['endpoint'].items() if k not in ['Bloom','HeaderRLP']},indent=2))
