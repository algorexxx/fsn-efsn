import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
protocol = workspace / 'tmp/peer-purchase-retry-2026-09-27'
working = workspace / 'tmp/full-state-peer-reconnect-2026-09-27'
source = workspace / 'tmp/full-state-existing-funds-2026-09-27'
baseline = 'cf70290f03b3be509602107bbfbdba73315be201'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    return path.read_text(encoding='utf-8')


def retain(source_path, target):
    data = source_path.read_bytes()
    if target.exists():
        assert target.read_bytes() == data, str(target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=workspace, text=True).strip()


assert read(evidence / 'package-build-exit.txt').strip() == '1'
assert 'undefined: ethdb.MemDatabase' in read(evidence / 'package-build.txt')
assert read(evidence / 'build.txt') == read(evidence / 'live-build.txt') == ''
assert read(evidence / 'admission-build.txt') == ''
assert read(evidence / 'binary.sha256').split()[0] == digest(protocol / 'protocol-tests')
assert read(evidence / 'live-binary.sha256').split()[0] == digest(protocol / 'live-tests')
assert read(evidence / 'admission-binary.sha256').split()[0] == digest(protocol / 'admission-tests')
times = {}
for label, name, status, passes in [('protocol', 'TestRestartPeerPurchaseRetry', 'PASS', 4), ('live', 'TestFullStatePurchasePeerReconnect', 'FAIL', 0), ('cold', 'TestFullStateFundingColdDiagnosis', 'PASS', 7), ('admission', 'TestFullStateReconnectHistoricalAdmission', 'PASS', 1)]:
    log = read(evidence / (label + '-race.txt'))
    assert int(read(evidence / (label + '-exit.txt'))) == int(status == 'FAIL')
    assert log.endswith(status + '\n') and 'WARNING: DATA RACE' not in log and '--- SKIP:' not in log
    assert log.count('--- FAIL:') == int(status == 'FAIL')
    assert log.count('--- PASS: ' + name) == passes
    times[label] = float(re.search(r'--- ' + status + ': ' + name + r' \(([0-9.]+)s\)', log)[1])
proof = json.loads(read(evidence / 'source-copy.json'))
assert proof['Files'] == 304 and proof['Bytes'] == 573895030
for path, expected in proof['SHA256'].items():
    assert digest(source / 'verifier' / path) == expected, path
live_proof = json.loads(read(evidence / 'source-copies-SHA256.json'))
assert len(live_proof) == 612
for path, expected in live_proof.items():
    assert digest(source / path) == expected, path
original = json.loads(read(source / 'diagnostic-saved-producer.json'))
saved_hash = original['Transaction']['hash']
for mode, stages in [('same-peer-resend', 6), ('ready-reconnect', 7), ('early-reconnect', 9)]:
    path = protocol / (mode + '.jsonl')
    observations = [json.loads(line) for line in read(path).splitlines()]
    assert len(observations) == stages
    first, last = observations[0], observations[-1]
    assert first['Stage'] == 'before-send' and not first['SenderKnown'] and not first['ReceiverKnown']
    assert last['Stage'] == 'exact-purchase-admitted-after-readiness'
    assert last['SenderStatus'] == last['ReceiverStatus'] == 2
    assert last['AcceptTxs'] == 1 and last['SenderKnown'] and last['ReceiverKnown']
    records = last['Admissions']
    assert len(records) == 3
    assert [r['Height'] for r in records] == [15130098, 15130098, 15130099]
    assert [r['Error'] for r in records] == ['BuyTicket start must be lower than latest block time + 3 hour'] * 2 + ['']
    assert all(r['PeerKnown'] and r['Hash'] == saved_hash and r['Bytes'] == original['Saved'] for r in records)
    assert observations[1]['ConnectionWrites'] == observations[2]['ConnectionWrites'] == 1
    assert observations[4]['ConnectionWrites'] == 3 and observations[4]['ReceiverStatus'] == 0
    if mode == 'early-reconnect':
        assert observations[6]['AcceptTxs'] == 0 and observations[6]['SenderKnown'] and not observations[6]['ReceiverKnown']
        assert observations[7]['AcceptTxs'] == 1 and observations[7]['ReceiverStatus'] == 0
        assert len(observations[6]['Admissions']) == len(observations[7]['Admissions']) == 2
        assert observations[6]['ConnectionWrites'] == observations[7]['ConnectionWrites'] == 1
    retain(path, evidence / path.name)
result = json.loads(read(working / 'funding-diagnosis.json'))
assert result['BothColdPoolsAccepted'] and result['BothCanonicalNoncesMatch'] and not result['LiveContinuationPassed']
assert result['Blocks'] == int(result['Final']['number'], 16) - 15130080
assert result['Blocks'] == 44 and result['Final']['hash'] == '0xd94c46f9d7993ebbd0ac7e6d984e36b280724b30028edd04166e0b7d59f5a8f8'
donation = '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf'
entrant = '0x6813eb9362372eef6200f3b1dbc3f819671cba69'
unready = json.loads(read(working / 'unready-recipient.json'))
assert donation not in unready['Pending'] and donation not in unready['Queued']
assert (working / 'producer-diagnostic.json').read_bytes() == (working / 'verifier-diagnostic.json').read_bytes()
accounts = json.loads(read(working / 'producer-diagnostic.json'))
assert accounts['Accounts'][donation]['Nonce'] == 9 and accounts['Accounts'][entrant]['Nonce'] == 38
included = set()
for number in range(1, result['Blocks'] + 1):
    for suffix in ['.json', '.rlp']:
        path = working / 'diagnostic-blocks' / f'block-{number:02d}{suffix}'
        if number <= 31:
            assert digest(path) == digest(source / 'diagnostic-blocks' / path.name)
        else:
            retain(path, evidence / 'blocks' / path.name)
    if number > 31:
        block = json.loads(read(working / 'diagnostic-blocks' / f'block-{number:02d}.json'))
        for receipt in block['Receipts']:
            assert receipt['status'] == '0x1'
            included.add(receipt['transactionHash'])
original_entrant = json.loads(read(source / 'diagnostic-saved-verifier.json'))
assert saved_hash in included and original_entrant['Transaction']['hash'] in included
assert all(tx['hash'] not in included for tx in result['SavedPurchases'])
trace = [json.loads(line) for line in read(working / 'delivery-pools.jsonl').splitlines()]
last = trace[-1]['Nodes']
assert all(node['Header']['hash'] == result['Final']['hash'] for node in last)
assert last[0]['Own']['Nonce'] == 9 and last[1]['Own']['Nonce'] == 38
assert last[0]['Pending'][donation][0]['hash'] == result['SavedPurchases'][0]['hash']
assert donation not in last[1]['Pending'] and donation not in last[1]['Queued']
for name in ['unready-recipient.json', 'reconnected-recipient.json', 'delivery-pools.jsonl', 'funding-diagnosis.json', 'diagnostic-saved-producer.json', 'diagnostic-saved-verifier.json']:
    retain(working / name, evidence / name)
for role in ['producer', 'verifier']:
    assert (working / ('initial-diagnostic-saved-' + role + '.json')).read_bytes() == (source / ('diagnostic-saved-' + role + '.json')).read_bytes()
retain(working / 'producer-diagnostic.json', evidence / 'accounts-final.json')
assert 'without recipient RPC submission' in read(evidence / 'live-race.txt')
assert 'nonces >= [9 27]' in read(evidence / 'live-race.txt')
assert 'participant ledger passed:' in read(evidence / 'cold-race.txt')
assert len(re.findall(r'participant ledger retreat block=', read(evidence / 'cold-race.txt'))) == 2
admissions = json.loads(read(working / 'historical-admission-complete.json'))
assert [int(r['Header']['number'], 16) for r in admissions] == [15130112, 15130113, 15130124]
assert [r['CanonicalNonce'] for r in admissions] == [9, 9, 9]
assert [r['PoolStatus'] for r in admissions] == [0, 2, 2]
assert admissions[0]['RemoteAdmissionError'] == 'insufficient balance(21978001816000000000), need 5000000021224000021224 = (gas:21224 * price:1000000001 + value:5000000000000000000000 + fee:0)'
assert all(r['RemoteAdmissionError'] == '' for r in admissions[1:])
assert all(r['Transaction'] == result['SavedPurchases'][0]['hash'] for r in admissions)
assert len({r['Saved'] for r in admissions}) == 1
for name in ['historical-admission-complete.json', 'historical-admission-15130112.json', 'historical-admission-15130113.json', 'historical-admission-15130124.json']:
    retain(working / name, evidence / name)
sources = set(json.loads(read(workspace / 'docs/evidence/restart-purchase-delivery-2026-09-27/identities.json'))['sources'])
sources |= {'eth/' + name for name in read(evidence / 'production-files.txt').split()}
sources |= {'eth/restart_purchase_retry_test.go'}
assert not [p for p in git('diff', '--name-only', baseline).splitlines() if (p.endswith('.go') and not p.endswith('_test.go')) or p in ['go.mod', 'go.sum']]
identities = {'baseline': baseline, 'runtime_changed': False, 'protocol_build_scope': 'Exact selected platform production Go files from eth plus restart_purchase_retry_test.go; legacy package tests do not compile and are not claimed passing. No production overlay.', 'sources': {name: {'git_blob': git('hash-object', '--path=' + name, name), 'sha256': digest(workspace / name)} for name in sorted(sources)}, 'live_and_cold_build_test_override': {'tests/restart/full_state_delivery_linux_test.go': digest(evidence / 'live-full_state_delivery_linux_test.go.txt')}, 'admission_build': 'Final source adds the historical nonce-9 admission case and shares the existing historical admission helper; no production changes.'}
summary = {'seconds': times, 'ordered_protocol_cases_passed': 3, 'original_historical_connection_observed': False, 'same_peer_explicit_resend_passed': True, 'ready_pending_replay_passed': True, 'early_reconnect_loss_reproduced': True, 'live_original_purchase_peer_recovery_passed': True, 'live_both_owner_replenishment_passed': False, 'next_purchase_missing_from_receiver_pool': True, 'next_purchase_historical_funding_rejection_reproduced': True, 'cold_pools_and_ledger_passed': True, 'canonical_blocks_audited': result['Blocks'], 'unchanged_prefix_blocks': 31, 'additional_blocks': result['Blocks'] - 31, 'original_files_rechecked': len(live_proof), 'new_funding': False, 'nonce_gap_exercised': False, 'complete_eth_package_tests_passed': False}
for name, value in [('identities.json', identities), ('results.json', summary)]:
    (evidence / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
print(json.dumps(summary, indent=2))
print(f'{len(sources)} source identities; {len(files)} evidence checksums')
