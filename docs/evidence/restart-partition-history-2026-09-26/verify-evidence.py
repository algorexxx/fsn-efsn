import json
import re
import runpy
from pathlib import Path

ctx = runpy.run_path(str(Path(__file__).with_name('verify-history.py')))
workspace, evidence, working = (ctx[name] for name in ['workspace', 'evidence', 'working'])
digest, git, retain, read = (ctx[name] for name in ['digest', 'git', 'retain', 'read'])
baseline = '12651ceaf3c1bf35ee8bda9bfd1ff95ccdfa1357'
assert baseline in read('environment.txt')
logs = {name: read(name + '-race.txt') for name in ['partition', 'diagnostic', 'post-sync', 'original-fork']}
expected = [('partition', 'TestFullStatePartitionRepair', 1), ('diagnostic', 'TestFullStatePartitionColdDiagnosis', 0), ('post-sync', 'TestFullStatePostSyncAccounting', 0), ('original-fork', 'TestFullStateOriginalForkHistory', 0)]
seconds = {}
for name, test, code in expected:
    log = logs[name]
    status = 'FAIL' if code else 'PASS'
    assert int(read(name + '-exit.txt')) == code and log.endswith(status + '\n')
    assert 'WARNING: DATA RACE' not in log and '--- SKIP:' not in log
    assert log.count('--- FAIL:') == code
    seconds[name] = float(re.search(r'^--- ' + status + ': ' + test + r' \(([0-9.]+)s\)', log, re.M)[1])
assert 'isolated producer did not advance multiple blocks' in logs['partition']
assert 'partition sync sample' not in logs['partition'] and not (working / 'repair').exists()
for name in ['prepare-producer', 'prepare-verifier', 'history-producer', 'history-verifier', 'fund-producer', 'fund-verifier']:
    assert f'--- PASS: TestFullStatePartitionRepair/{name} (' in logs['partition']
for name in ['post-sync', 'original-fork']:
    assert read(name + '-build.txt') == ''
    assert read(name + '-binary.sha256').split()[0] == digest(workspace / 'tmp/partition-history-2026-09-26' / ('tests-' + name))
sync = json.loads((working / 'cold-sync-diagnosis.json').read_text(encoding='utf-8'))
assert [s['Number'] for s in sync['Before']] == [15130089, 15130096]
assert [int(s['TD'],16) for s in sync['Before']] == [63370514683, 63370514696]
assert sync['ExplicitDownloader'] == 'not attempted' and sync['Automatic'] == sync['After']
assert sync['After'][0] == sync['After'][1] == sync['Before'][1]
final = sync['After'][0]['Hash']
for phase in ['Before', 'After']:
    assert all(not s['Mining'] and not s['AutoBuy'] and s['Signatures'] == 0 for s in sync[phase])
assert 'matched=true' in logs['diagnostic'] and 'Found common ancestor' in logs['diagnostic']
assert 'number=15,130,089' in logs['diagnostic']
assert 'post-sync complete-state accounting passed:' in logs['post-sync']
assert logs['diagnostic'].count('participant ledger passed:') == 2
assert logs['post-sync'].count('participant ledger passed:') == 1
funds = {}
for role in ['producer','verifier']:
    funds[role] = json.loads((working / ('post-sync-' + role + '.json')).read_text(encoding='utf-8'))
    old = json.loads((working / ('cold-' + role + '.json')).read_text(encoding='utf-8'))
    assert funds[role]['Saved'] == old['Saved'] and funds[role]['Header']['hash'] == final
    assert len(bytes.fromhex(old['Saved'][2:])) == 117
    for prefix in ['cold-', 'post-sync-']:
        retain(working / (prefix + role + '.json'), evidence / (prefix + role + '.json'))
donation, entrant = funds['producer'], funds['verifier']
assert donation['Nonce'] == donation['SavedNonce'] == 7 and donation['OwnerTickets'] == 0
assert donation['LiquidWei'] == '2021665544264000000000' and donation['CoverageAtHeadWei'] == donation['CoverageNowWei'] == '0'
assert donation['RequiredLiquidWei'] == '5000000042448000000000' and donation['PoolAdmission'].startswith('insufficient balance')
assert entrant['Nonce'] == entrant['SavedNonce'] == 11 and entrant['OwnerTickets'] == 1
assert entrant['CoverageAtHeadWei'] == entrant['CoverageNowWei'] == '5000000000000000000000'
assert entrant['RequiredLiquidWei'] == '42448000000000' and entrant['PoolAdmission'] == 'accepted'
branches = {}
for source, label, count in [('cold-producer','before-producer',9),('cold-verifier','before-verifier',16),('blocks','canonical',16)]:
    paths = sorted((working/source).glob('block-*.json'))
    assert len(paths) == count
    prior = None
    txs = 0
    for n,path in enumerate(paths,1):
        ledger=json.loads(path.read_text(encoding='utf-8'))
        assert path.name == f'block-{n:02d}.json' and int(ledger['Header']['number'],16) == 15130080+n
        if prior:
            assert ledger['Header']['parentHash'] == prior
        prior=ledger['Header']['hash']
        assert all(int(receipt['status'],16) == 1 for receipt in ledger['Receipts'])
        txs += len(ledger['Receipts'])
        for suffix in ['.json','.rlp']:
            retain(path.with_suffix(suffix), evidence / 'artifacts' / label / path.with_suffix(suffix).name)
        if source == 'blocks':
            assert digest(path) == digest(working / 'cold-verifier' / path.name)
    branches[label]={'blocks':count,'head':prior,'transactions':txs}
assert branches['canonical']['head'] == final and branches['before-producer']['head'] == sync['Before'][0]['Hash']
for name in ['fixture.json','handover.json']:
    retain(working/'producer'/name,evidence/'artifacts'/name)
retain(working/'cold-sync-diagnosis.json',evidence/'cold-sync-diagnosis.json')
recheck_root=workspace/'tmp/full-state-partition-2026-09-26'
recheck=json.loads((recheck_root/'history-recheck.json').read_text(encoding='utf-8'))
old=json.loads((workspace/'docs/evidence/restart-full-state-partition-2026-09-26/cold-sync-diagnosis.json').read_text(encoding='utf-8'))
assert recheck['Before'] == recheck['After'] == old['Before']
assert recheck['RemoteStored'] == old['Before'][1]['Hash']
assert 'fromnum=15,085,106' in logs['original-fork'] and 'Found common ancestor' in logs['original-fork']
assert 'Multiple headers for single request' not in logs['original-fork']
retain(recheck_root/'history-recheck.json',evidence/'original-fork-recheck.json')
for role in ['producer','verifier']:
    path=recheck_root/role/'history-installed.json'
    assert json.loads(path.read_text(encoding='utf-8')) == ctx['exported']
    retain(path,evidence/('original-fork-'+role+'-history-installed.json'))
sources=list(json.loads((workspace/'docs/evidence/restart-full-state-partition-2026-09-26/identities.json').read_text(encoding='utf-8'))['sources'])
sources += ['tests/restart/full_state_history_linux_test.go','tests/restart/full_state_post_sync_linux_test.go','tests/restart/full_state_original_history_linux_test.go','core/types/block.go','core/rawdb/accessors_chain.go']
sources=sorted(set(sources))
assert not [p for p in git('diff','--name-only',baseline).splitlines() if (p.endswith('.go') and not p.endswith('_test.go')) or p in ['go.mod','go.sum']]
identities={'baseline':baseline,'runtime_changed':False,'sources':{name:{'git_blob':git('hash-object','--path='+name,name),'sha256':digest(workspace/name)} for name in sources},'build_order':['initial history extractor','corrected history extractor and live partition','post-sync accounting test added','original-fork history test added'],'initial_override':{'source':'tests/restart/full_state_history_linux_test.go','retained':'initial-full_state_history_linux_test.go.txt','sha256':digest(evidence/'initial-full_state_history_linux_test.go.txt')}}
results={'seconds':seconds,'live_partition_passed':False,'manual_repair_reached':False,'heavier_stopped_peer_sync_passed':True,'original_missing_header_recheck_passed':True,'equal_weight_heads_converged':False,'canonical_cold_ledgers_match':True,'donation_failure':'insufficient funds with correct nonce and zero tickets','branches':branches,'history':ctx['exported'],'source_files_unchanged':230}
for name,value in [('identities.json',identities),('results.json',results)]:
    (evidence/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
files=sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files),encoding='utf-8',newline='\n')
print(f'Verified live failure, ordinary stopped sync, exact missing-header recheck, all three cold branch ledgers, saved-record/funding checks, {len(sources)} source identities and {len(files)} evidence checksums')
