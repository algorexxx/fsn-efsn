from pathlib import Path
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = HERE/'qualification'
r = json.loads((Q/'run.json').read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert r['completed'] and not r.get('failures') and not r.get('stop_reason')
for name in ['replay_passed','inspect_passed','cold_target_bytes_unchanged','backup_unchanged','baselines_unchanged','selected_unchanged','candidate_unchanged','inputs_unchanged']:
    assert r[name], name
assert r['uid'] == 1000 and r['namespace'] != r['parent_namespace']
assert r['mount_namespace'] != r['parent_mount_namespace']
assert len(r['links'].splitlines()) == 1 and r['links'].startswith('lo ') and 'DOWN' in r['links']
for name in ['backup_mount','closed_mount']:
    assert 'ro' in r[name]['options'].split(',')
assert r['target'] == '/home/rehearsal/replay/candidate-ticket-encoding-100000'
for name,digest in r['input_sha256'].items():
    assert sha(HERE/name) == digest,name
prior = HERE.parent/'restart-ticket-encoder-regressions-2026-10-08'
pr = json.loads((prior/'qualification/run.json').read_text(encoding='utf-8'))
assert r['toolchain']['go_binary_sha256'] == pr['toolchains']['modern']['go_binary_sha256']
env = r['toolchain']['go_env']
assert env['GOVERSION'] == 'go1.27.1' and env['GOENV'] == '' and env['GOFLAGS'] == '-mod=readonly'
assert env['GOOS'] == 'linux' and env['GOARCH'] == 'amd64' and env['GOAMD64'] == 'v1'
assert env['GOPROXY'] == env['GOSUMDB'] == 'off' and env['GOTOOLCHAIN'] == 'local'
runtime = r['runtime_environment']
assert runtime['GOMAXPROCS'] == '2' and runtime['FUSION_RESTART_REPLAY_END'] == '100000'
assert runtime['FUSION_RESTART_FULL_AUDIT'] == '1' and runtime['FUSION_RESTART_HOST_STORAGE'] == '/mnt/d'
assert 'FUSION_RESTART_REPLAY_RESUME' not in runtime
previous_count = 0
for name,digest in r['previous_manifest_sha256'].items():
    directory = HERE.parent/name
    assert sha(directory/'SHA256SUMS') == digest
    for line in (directory/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,relative = line.split(None,1)
        assert sha(directory/relative) == expected,(name,relative)
        previous_count += 1
assert previous_count == r['previous_files_verified']
base = json.loads((HERE.parent/'restart-release-jwt-2026-10-04/node-inventory.json').read_text(encoding='utf-8'))
assert r['selected_inventory'] == base
candidate = json.loads((HERE.parent/'restart-ticket-encoder-candidate-v2-2026-10-08/qualification/run.json').read_text(encoding='utf-8'))
expected = dict(base,**candidate['runtime_input_sha256'])
helpers = (Q/'helpers_test.go').read_bytes()
assert len(r['helper_extractions']) == 5
for helper in r['helper_extractions']:
    path = REPO/helper['source']
    assert sha(path) == helper['source_sha256']
    body = b''.join(path.read_bytes().splitlines(keepends=True)[helper['start_line']-1:helper['end_line']])
    assert hashlib.sha256(body).hexdigest() == helper['body_sha256']
    assert helpers.count(body) == 1
for name,digest in r['test_input_sha256'].items():
    path = Q/'helpers_test.go' if name.endswith('/helpers_test.go') else HERE/'details_test.go' if name.endswith('/details_test.go') else REPO/name
    assert sha(path) == digest,name
expected.update(r['test_input_sha256'])
assert r['candidate_inventory'] == expected
commands = r['commands']
assert [c['name'] for c in commands] == ['patch-check','patch-apply','build','build-info','reference','replay','cold-head','cold-details']
for command in commands:
    assert command['exit'] == 0
    assert not (Q/(command['name']+'.stderr.txt')).read_bytes()
    assert command['started'] <= command['finished']
assert commands[4]['finished'] <= commands[5]['started']
assert commands[5]['finished'] <= commands[6]['started'] <= commands[7]['started']
for name,test in [('reference','TestCandidateReplayReference'),('replay','TestPreservedHistoryReplay'),('cold-head','TestPreservedReplayHeadReadOnly'),('cold-details','TestCandidateReplayColdDetails')]:
    output = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert output.endswith('PASS\n') and '--- FAIL:' not in output and '--- SKIP:' not in output
    assert re.findall(r'^--- PASS: (\S+) \(',output,re.M) == [test]
reference = r['endpoint_observations']['reference']
cold = r['endpoint_observations']['cold-details'].copy()
ticket_count = cold.pop('TicketCount')
assert ticket_count > 0 and cold == reference
for name,observed in [('reference',reference),('cold-details',r['endpoint_observations']['cold-details'])]:
    output = (Q/(name+'.stdout.txt')).read_text(encoding='utf-8')
    assert json.loads(re.search(r'candidate endpoint observation: (\{.*\})',output)[1]) == observed
assert reference['Number'] == 100000 and reference['Receipts'] == reference['Transactions']
identity = json.loads((Q/'replay-identity.json').read_text(encoding='utf-8'))
assert identity['Format'] == 1 and identity['ExecutableHash'] == r['binary_sha256']
assert identity['SourceGenesis'] == '0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a'
assert identity['SourceHead'] == '0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f'
assert r['target_before_cold_sha256']['replay-identity.json'] == sha(Q/'replay-identity.json')
output = (Q/'replay.stdout.txt').read_text(encoding='utf-8')
assert 'legacyCheckpointRangeEnd=2680000' in output
assert 'replay starting at height=0 hash='+identity['SourceGenesis']+' resume=false' in output
endpoint = re.search(r'replay matched: height=(\d+) hash=(0x[0-9a-f]+) root=(0x[0-9a-f]+) ticketCommitment=(0x[0-9a-f]+) tickets=(\d+)',output)
assert endpoint and int(endpoint[1]) == 100000 and endpoint[2] == reference['Hash'] and endpoint[3] == reference['Root'] and endpoint[4] == reference['TicketCommitment'] and int(endpoint[5]) == ticket_count
cold_log = (Q/'cold-head.stdout.txt').read_text(encoding='utf-8')
assert 'closed replay matched: height=100000 hash='+reference['Hash']+' root='+reference['Root']+' ticketCommitment='+reference['TicketCommitment'] in cold_log
for label,observation in [('backup-before',r['backup_before']),('backup-after',r['backup_after'])] + [('baseline-'+height+'-'+phase,r['baseline_'+phase][height]) for phase in ['before','after'] for height in ['3300000','3600000']]:
    raw = gzip.decompress((Q/(label+'.json.gz')).read_bytes())
    rows = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == observation['metadata_sha256']
    assert len(rows) == observation['files'] and sum(row[1] for row in rows) == observation['logical_bytes']
assert r['backup_before'] == r['backup_after'] and r['baseline_before'] == r['baseline_after']
assert r['backup_before']['files'] == 56107 and r['backup_before']['logical_bytes'] == 117170022674
historical = json.loads((HERE.parent/'restart-ticket-compression-2026-10-08/qualification/run.json').read_text(encoding='utf-8'))
assert r['backup_before'] == historical['backup_after']
assert r['closed_allocated_bytes'] < 4*1024**3
assert r['capacity_bytes']['/home/rehearsal/results'] > 30*1024**3 and r['capacity_bytes']['/mnt/d'] > 60*1024**3
assert r['remaining_bytes']['/home/rehearsal/results'] > 20*1024**3 and r['remaining_bytes']['/mnt/d'] > 50*1024**3
assert all(m['exit'] == 0 and not m['stderr'] for m in r['size_measurements'])
result = {'pass':True,'commands':len(commands),'previous_files_verified':previous_count,'started':r['started'],'replay_started':commands[5]['started'],'replay_finished':commands[5]['finished'],'finished':r['finished'],'endpoint':dict(reference,TicketCount=ticket_count),'binary_sha256':r['binary_sha256'],'target_files_hashed':len(r['target_before_cold_sha256']),'closed_allocated_bytes':r['closed_allocated_bytes'],'remaining_bytes':r['remaining_bytes'],'source_files_preserved':r['backup_before']['files'],'baseline_metadata_preserved':True,'legacy_checkpoint_end':2680000}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key != 'endpoint'},indent=2))
print(json.dumps({key:value for key,value in result['endpoint'].items() if key not in ['Bloom','HeaderRLP']},indent=2))
