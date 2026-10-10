from pathlib import Path
import difflib
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
Q = HERE/'qualification'
ATTEMPT = HERE.parent/'restart-ticket-encoder-job-6300000-2026-10-10'
BASE = HERE.parent/'restart-ticket-encoder-replay-100000-2026-10-08'
REPLAY_SHA = 'b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


r = json.loads((Q/'run.json').read_text(encoding='utf-8'))
prior = json.loads((ATTEMPT/'qualification/run.json').read_text(encoding='utf-8'))
assert r['completed'] and r['inspect_passed'] and not r.get('failures')
assert len(r['preservation_checks']) == 12 and all(r['preservation_checks'].values())
assert not prior['completed'] and not prior.get('replay_passed')
assert prior['stop_reason'] == 'declared target allocation allowance reached'
assert prior['additional_preservation_checks']['prior_stop_unchanged']
assert [c['exit'] for c in prior['commands']] == [0,0,0,0,1]
assert all(prior[n] for n in ['backup_unchanged','baselines_unchanged','selected_unchanged','candidate_unchanged','inputs_unchanged','resume_verified'])
assert len(prior['additional_preservation_checks']) == 10 and all(prior['additional_preservation_checks'].values())
output = (ATTEMPT/'qualification/replay.stdout.txt').read_text(encoding='utf-8')
assert re.findall(r'replay stopped by stop file before block (\d+);',output) == ['5600033']
assert output.endswith('FAIL\n') and 'replay matched:' not in output
assert re.findall(r'^--- FAIL: (\S+)',output,re.M) == ['TestPreservedHistoryReplay']
assert 'legacyCheckpointRangeEnd=2680000' in output
assert r['inspection_height'] == 5600032 and r['requested_attempt_height'] == 6300000
assert r['uid'] == 1000 and r['namespace'] != r['parent_namespace'] and r['mount_namespace'] != r['parent_mount_namespace']
assert len(r['links'].splitlines()) == 1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
for name in ['backup_mount','checkpoint_mount','closed_mount']:
    assert 'ro' in r[name]['options'].split(',')
for record,directory in [(prior,ATTEMPT/'inputs'),(r,HERE)]:
    for name,digest in record['input_sha256'].items():
        assert sha(directory/name) == digest,name
count = 0
for name,digest in r['previous_manifest_sha256'].items():
    directory = HERE.parent/name
    assert sha(directory/'SHA256SUMS') == digest
    for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,relative = line.split(None,1)
        assert sha(directory/relative) == expected,(name,relative)
        count += 1
assert count == r['previous_files_verified'] == prior['previous_files_verified']+len((ATTEMPT/'SHA256SUMS').read_text(encoding='utf-8').splitlines())
assert r['imported_runner_sha256'] == sha(BASE/'run.py')
assert r['checkpoint_before_sha256'] == prior['recovery_checkpoint_sha256']
recovery = json.loads((HERE.parent/r['recovery_bundle']/'qualification/run.json').read_text(encoding='utf-8'))
assert r['checkpoint_before_sha256'] == recovery['target_before_cold_sha256']
assert r['selected_inventory'] == prior['selected_inventory'] and r['candidate_inventory'] == prior['candidate_inventory']
assert r['binary_sha256'] == prior['binary_sha256'] == REPLAY_SHA
assert r['toolchain']['go_binary_sha256'] == prior['toolchain']['go_binary_sha256']
env = r['toolchain']['go_env']
assert env['GOVERSION'] == 'go1.27.1' and env['GOENV'] == '' and env['GOFLAGS'] == '-mod=readonly'
assert env['GOPROXY'] == env['GOSUMDB'] == 'off' and env['GOTOOLCHAIN'] == 'local'
runtime = r['runtime_environment']
assert runtime['GOMAXPROCS'] == '2' and runtime['FUSION_RESTART_INSPECT_REPLAY_HEIGHT'] == '5600032'
assert 'FUSION_RESTART_REPLAY_RESUME' not in runtime and 'FUSION_RESTART_REPLAY_END' not in runtime
identity = (Q/'replay-identity.json').read_bytes()
assert sha(Q/'replay-identity.json') == r['checkpoint_identity_sha256'] == prior['checkpoint_identity_sha256']
assert r['target_before_cold_sha256']['replay-identity.json'] == r['checkpoint_identity_sha256']
assert json.loads(identity)['ExecutableHash'] == REPLAY_SHA
assert sha(Q/'attempt-STOP') == sha(ATTEMPT/'qualification/STOP') == r['stop_sha256']
old = (ATTEMPT/'inputs/details_test.go').read_bytes()
new = old.replace(b'const height = uint64(6300000)',b'const height = uint64(5600032)',1)
assert (HERE/'details_test.go').read_bytes() == new and old != new
assert (HERE/'observer-change.patch').read_text(encoding='utf-8') == ''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/details_test.go',tofile='b/details_test.go'))
assert sha(Q/'observer-overlay.json') == r['observer_overlay_sha256']
commands = r['commands']
assert [c['name'] for c in commands] == ['observer-build','observer-build-info','reference','cold-head','cold-details']
for c in commands:
    assert c['exit'] == 0 and c['started'] <= c['finished']
    assert not (Q/(c['name']+'.stderr.txt')).read_bytes()
assert commands[2]['finished'] <= commands[3]['started'] <= commands[3]['finished'] <= commands[4]['started']
for name,test,binary in [('reference','TestCandidateReplayReference','observer'),('cold-head','TestPreservedReplayHeadReadOnly','replay-tests'),('cold-details','TestCandidateReplayColdDetails','observer')]:
    c = next(c for c in commands if c['name'] == name)
    assert any(arg.endswith('/bin/'+binary) for arg in c['argv'])
    assert '-test.run=^'+test+'$' in c['argv']
    log = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert log.endswith('PASS\n') and '--- FAIL:' not in log and '--- SKIP:' not in log
    assert re.findall(r'^--- PASS: (\S+) \(',log,re.M) == [test]
reference = r['endpoint_observations']['reference']
cold = r['endpoint_observations']['cold-details'].copy()
tickets = cold.pop('TicketCount')
assert tickets > 0 and cold == reference and reference['Number'] == 5600032
assert reference['Transactions'] == reference['Receipts']
for name in ['reference','cold-details']:
    log = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert json.loads(re.search(r'candidate endpoint observation: (\{.*\})',log)[1]) == r['endpoint_observations'][name]
assert 'closed replay matched: height=5600032 hash='+reference['Hash']+' root='+reference['Root']+' ticketCommitment='+reference['TicketCommitment'] in (Q/'cold-head.stdout.txt').read_text(encoding='utf-8')
for label,observed in [('backup-before',r['backup_before']),('backup-after',r['backup_after'])]+[('baseline-'+h+'-'+phase,r['baseline_'+phase][h]) for phase in ['before','after'] for h in ['3300000','3600000']]:
    raw = gzip.decompress((Q/(label+'.json.gz')).read_bytes())
    rows = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == observed['metadata_sha256']
    assert len(rows) == observed['files'] and sum(row[1] for row in rows) == observed['logical_bytes']
assert r['backup_before'] == r['backup_after'] == prior['backup_after']
assert r['baseline_before'] == r['baseline_after'] == prior['baseline_after']
size = r['closed_size_measurement']
assert size['exit'] == 0 and not size['stderr']
fields = size['stdout'].split()
assert len(fields) == 2 and fields[1] == r['closed_mount']['target']
allocated = int(fields[0])
assert allocated > 0
assert r['result_logical_bytes'] < 256*1024**2
assert r['starting_capacity_bytes']['/home/rehearsal/results'] > 21*1024**3 and r['starting_capacity_bytes']['/mnt/d'] > 51*1024**3
assert [c['name'] for c in r['command_capacity']] == [c['name'] for c in commands]
assert all(c['free_bytes']['/home/rehearsal/results'] > 20*1024**3 and c['free_bytes']['/mnt/d'] > 50*1024**3 for c in r['command_capacity'])
assert r['remaining_bytes']['/home/rehearsal/results'] > 20*1024**3 and r['remaining_bytes']['/mnt/d'] > 50*1024**3
result = {'pass':True,'scope':'read-only stopped-checkpoint inspection; requested replay remains incomplete','attempt_completed':False,'requested_height':6300000,'cold_verified_height':5600032,'commands':len(commands),'previous_files_verified':count,'checkpoint_files_verified':len(r['checkpoint_before_sha256']),'target_files_hashed':len(r['target_before_cold_sha256']),'replay_binary_sha256':REPLAY_SHA,'observer_binary_sha256':r['observer_binary_sha256'],'endpoint':dict(reference,TicketCount=tickets),'closed_allocated_bytes':allocated,'remaining_bytes':r['remaining_bytes'],'started':r['started'],'finished':r['finished'],'legacy_checkpoint_end':2680000}
(HERE/'verification.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'))
print(json.dumps({k:v for k,v in result.items() if k!='endpoint'},indent=2))
print(json.dumps({k:v for k,v in result['endpoint'].items() if k not in ['Bloom','HeaderRLP']},indent=2))
