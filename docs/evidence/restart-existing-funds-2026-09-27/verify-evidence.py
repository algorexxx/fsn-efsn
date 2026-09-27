import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
working = workspace / 'tmp/full-state-existing-funds-2026-09-27'
prior = workspace / 'docs/evidence/restart-partition-history-2026-09-26'
baseline = '26b416c986cfb442280e96c564b9069ea7e8c591'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    return path.read_text(encoding='utf-8')


def retain(source, destination):
    data = source.read_bytes()
    if destination.exists():
        assert destination.read_bytes() == data, str(destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=workspace, text=True).strip()


assert baseline in read(evidence / 'environment.txt')
assert all(read(evidence / name) == '' for name in ['build.txt', 'live-build.txt', 'start-order-build.txt', 'diagnosis-build.txt', 'ledger-build.txt'])
for label, binary in [('binary', 'tests'), ('live-binary', 'tests-live'), ('start-order-binary','tests-start-order'), ('diagnosis-binary','tests-diagnosis'), ('ledger-binary','tests-ledger')]:
    assert read(evidence / (label + '.sha256')).split()[0] == digest(workspace / 'tmp/existing-funds-2026-09-27' / binary)
log = read(evidence / 'recovery-race.txt')
assert read(evidence / 'recovery-exit.txt').strip() == '0'
assert log.endswith('PASS\n') and 'WARNING: DATA RACE' not in log and '--- SKIP:' not in log
assert log.count('--- PASS:') == 5
assert 'both cold canonical databases and every future interval reconcile' in log
seconds = float(re.search(r'--- PASS: TestFullStateFundingRecovery \(([0-9.]+)s\)', log)[1])
proof = json.loads(read(evidence / 'source-copy-SHA256.json'))
source = workspace / 'tmp/full-state-history-partition-2026-09-26'
for path, expected in proof.items():
    assert digest(source / path) == expected, path
assert len(proof) == 592
data = json.loads(read(working / 'funding-recovery.json'))
assert data['Source'] == '0x48212779e0851316084461094494cffcbb2c380362d1877a450c874913034291'
assert data['Blocks'] == 18 and not data['LiveMiningExercised'] and not data['NonceGapExercised']
assert len(data['Contributions']) == 2
assert [int(tx['value'],16) for tx in data['Contributions']] == [1200*10**18, 1800*10**18]
assert [int(tx['nonce'],16) for tx in data['Contributions']] == [233429,12]
assert [int(tx['nonce'],16) for tx in data['SavedPurchases']] == [7,11]
for phase in ['before', 'funded', 'recovered']:
    left = working / ('producer-' + phase + '.json')
    right = working / ('verifier-' + phase + '.json')
    assert left.read_bytes() == right.read_bytes()
    retain(left, evidence / ('accounts-' + phase + '.json'))
donation = '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf'
entrant = '0x6813eb9362372eef6200f3b1dbc3f819671cba69'
backup = '0x7e5f4552091a69125d5dfcb7b8c2659029395bdf'
states = {phase: json.loads(read(working / ('producer-' + phase + '.json')))['Accounts'] for phase in ['before', 'funded', 'recovered']}
assert states['before'][donation]['LiquidWei'] == '2021665544264000000000'
assert states['funded'][donation]['LiquidWei'] == '5021665544264000000000'
assert states['recovered'][donation]['LiquidWei'] == '21665501816000000000'
assert states['recovered'][entrant]['LiquidWei'] == '223852084448000000000'
assert states['recovered'][backup]['LiquidWei'] == '5752721845480158626'
assert states['recovered'][donation]['TicketCount'] == 1
for number in range(1,19):
    for suffix in ['.json','.rlp']:
        path = working / 'blocks' / f'block-{number:02d}{suffix}'
        if number <= 16:
            assert digest(path) == digest(prior / 'artifacts/canonical' / path.name)
        else:
            retain(path, evidence / 'blocks' / path.name)
for role in ['producer','verifier']:
    assert digest(working / ('source-' + role + '.json')) == digest(prior / ('post-sync-' + role + '.json'))
retain(working / 'funding-recovery.json', evidence / 'funding-recovery.json')
logs = {label: read(evidence / (label+'-race.txt')) for label in ['live','start-order','diagnosis','ledger']}
times = {}
for label, name, status in [('live','TestFullStateFundingLiveContinuation','FAIL'),('start-order','TestFullStateFundingStartOrder','FAIL'),('diagnosis','TestFullStateFundingColdDiagnosis','FAIL'),('ledger','TestFullStateFundingLedger','PASS')]:
    text = logs[label]
    assert text.endswith(status+'\n') and 'WARNING: DATA RACE' not in text and '--- SKIP:' not in text
    assert int(read(evidence / (label+'-exit.txt'))) == int(status == 'FAIL')
    times[label] = float(re.search(r'--- '+status+': '+name+r' \(([0-9.]+)s\)',text)[1])
    assert text.count('--- FAIL:') == int(status == 'FAIL')
assert 'continuous node=1 height=15130098' in logs['live'] and 'continuous node=2 height=15130098' in logs['live']
assert 'Next block doesn\'t have ticket, wait buy ticket' in logs['live']
assert 'continuous node=1 height=15130111' in logs['start-order'] and 'continuous node=2 height=15130111' in logs['start-order']
assert 'nonces >= [9 14]' in logs['start-order']
assert 'purchase receipt failed or ambiguous' in logs['diagnosis']
assert logs['diagnosis'].count('--- PASS:') == 6 and logs['diagnosis'].count('accepted both saved purchases nonce=8/26') == 2
assert 'participant mature conversion block=15130099' in logs['ledger']
assert 'participant ledger passed: blocks=28' in logs['ledger']
assert 'complete pre-purchase interval coverage minus funded ticket verified' in logs['ledger']
assert 'retreat block=19' not in logs['ledger']
original_ready = json.loads(read(working / 'live-ready-purchase.json'))
retry_before = json.loads(read(working / 'retry-before-purchases.json'))
retry_ready = json.loads(read(working / 'retry-ready-purchase.json'))
assert original_ready['Saved'] == retry_before[1]['Saved'] == retry_ready['Saved']
assert retry_before[0]['Saved'] == '0x' and retry_before[0]['Nonce'] == 8 and retry_before[1]['Nonce'] == 13
assert len(original_ready['Pending']) == len(retry_ready['Pending']) == 1
assert original_ready['Pending'][0]['hash'] == retry_ready['Pending'][0]['hash']
ledger = json.loads(read(working / 'funding-ledger.json'))
assert ledger['Blocks'] == 31 and ledger['LedgerPassed'] and not ledger['LiveContinuationPassed']
assert ledger['Final']['hash'] == '0xec993b33d085d74c03256109c866e825b7609a64a1a55a94b70a12daf27e54f9'
assert (working / 'producer-diagnostic.json').read_bytes() == (working / 'verifier-diagnostic.json').read_bytes()
after = json.loads(read(working / 'producer-diagnostic.json'))
assert after['Accounts'][donation]['Nonce'] == 8 and after['Accounts'][donation]['TicketCount'] == 0
assert after['Accounts'][entrant]['Nonce'] == 26 and after['Accounts'][entrant]['TicketCount'] == 1
assert after['Accounts'][donation]['LiquidWei'] == '21978023040000021224'
live_blocks = []
for number in range(1,32):
    for suffix in ['.json','.rlp']:
        path = working / 'diagnostic-blocks' / f'block-{number:02d}{suffix}'
        if number <= 18:
            assert digest(path) == digest(working / 'blocks' / path.name)
        else:
            retain(path,evidence / 'blocks' / path.name)
    entry = json.loads(read(working / 'diagnostic-blocks' / f'block-{number:02d}.json'))
    if number > 18:
        live_blocks.append(entry)
        assert len(entry['Receipts']) == 1 and entry['Receipts'][0]['status'] == '0x1'
        assert any(json.loads(bytes.fromhex(log['data'][2:])).get('TicketOwner') == entrant for log in entry['Receipts'][0]['logs'])
assert [entry['Header']['miner'] for entry in live_blocks] == [donation] + [entrant]*12
assert live_blocks[0]['Receipts'][0]['transactionHash'] == original_ready['Pending'][0]['hash']
assert len(live_blocks[0]['Receipts'][0]['logs']) == 2
aux = json.loads(bytes.fromhex(live_blocks[0]['Receipts'][0]['logs'][1]['data'][2:]))
assert aux['Value'] == 5000*10**18 and aux['LockType'] == 'TimeLockToAsset' and aux['To'] == entrant
for role, nonce in [('producer',8),('verifier',26)]:
    path = working / ('diagnostic-saved-'+role+'.json')
    saved = json.loads(read(path))
    assert saved['Nonce'] == nonce and int(saved['Transaction']['nonce'],16) == nonce
    assert saved['Header']['hash'] == ledger['Final']['hash']
    assert saved['Transaction']['hash'] in logs['start-order']
    retain(path,evidence/path.name)
for name in ['live-ready-purchase.json','retry-before-purchases.json','retry-ready-purchase.json','funding-ledger.json']:
    retain(working/name,evidence/name)
retain(working/'producer-diagnostic.json',evidence/'accounts-final.json')
sources = sorted(set(json.loads(read(prior / 'identities.json'))['sources']) | {
    'tests/restart/full_state_funding_recovery_linux_test.go',
    'tests/restart/full_state_funding_live_linux_test.go',
    'tests/restart/controlled_reserve_linux_test.go',
    'tests/restart/full_state_funding_diagnostic_linux_test.go',
    'tests/restart/handover_runway_test.go',
    'eth/backend.go','eth/handler.go','eth/sync.go','miner/worker.go','core/state/statedb.go','core/state_transition.go',
})
assert not [p for p in git('diff', '--name-only', baseline).splitlines() if (p.endswith('.go') and not p.endswith('_test.go')) or p in ['go.mod','go.sum']]
identities = {'baseline': baseline, 'runtime_changed': False, 'sources': {name: {'git_blob': git('hash-object', '--path='+name, name), 'sha256': digest(workspace / name)} for name in sources}, 'build_order': ['controlled recovery test', 'live continuation test added; cold capture helper gains a separate output path', 'start-order follow-up added to live file', 'cold diagnostic file added', 'mature-log validation added to participant audit and retained-ledger test added to diagnostic file'], 'controlled_build_outage_override': git('rev-parse', baseline + ':tests/restart/full_state_outage_linux_test.go'), 'source_snapshots': {name: digest(evidence/name) for name in ['initial-full_state_funding_live_linux_test.go.txt','initial-full_state_participant_ledger_test.go.txt','initial-full_state_funding_diagnostic_linux_test.go.txt']}, 'controlled_build_excludes': ['tests/restart/full_state_funding_live_linux_test.go','tests/restart/full_state_funding_diagnostic_linux_test.go'], 'live_and_start_order_build_excludes': ['tests/restart/full_state_funding_diagnostic_linux_test.go']}
results = {'controlled_seconds': seconds, 'seconds': times, 'controlled_recovery_passed': True, 'first_live_passed': False, 'start_order_live_passed': False, 'start_order_new_blocks': 13, 'canonical_blocks_audited': 31, 'cold_pool_checks_passed': True, 'independent_ledger_after_correction_passed': True, 'remote_rejection_captured': False, 'canonical_prefix_unchanged_blocks': 16, 'source_copy_files_unchanged': len(proof), 'additional_liquid_fsn': 3000, 'new_balance_created': False, 'nonce_gap_exercised': False}
for name, value in [('identities.json', identities), ('results.json', results)]:
    (evidence / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
print(f'Controlled recovery, both live failures, cold pool checks and corrected 31-block ledger verified; {len(proof)} source-copy files unchanged, {len(sources)} source identities and {len(files)} evidence checksums')
