import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
working = workspace / 'tmp/full-state-purchase-delivery-2026-09-27'
prior = workspace / 'docs/evidence/restart-existing-funds-2026-09-27'
baseline = '7f7697ba0c1ce769eb5862c24b17815b4746041a'


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
assert 'may not be used by non-root' in read(evidence / 'initial-build-launch-error.txt')
for label, binary in [('', 'tests'), ('corrected-', 'tests-corrected'), ('retained-', 'tests-retained')]:
    assert read(evidence / (label + 'build.txt')) == ''
    assert read(evidence / (label + 'binary.sha256')).split()[0] == digest(workspace / 'tmp/purchase-delivery-2026-09-27' / binary)
times = {}
for label, name, status in [('historical', 'TestFullStateDeliveryHistoricalAdmission', 'FAIL'), ('historical-corrected', 'TestFullStateDeliveryHistoricalAdmission', 'FAIL'), ('historical-retained', 'TestFullStateDeliveryHistoricalAdmission', 'PASS'), ('live-retained', 'TestFullStatePurchaseDirectDelivery', 'PASS')]:
    log = read(evidence / (label + '-race.txt'))
    assert log.endswith(status + '\n') and 'WARNING: DATA RACE' not in log and '--- SKIP:' not in log
    assert int(read(evidence / (label + '-exit.txt'))) == int(status == 'FAIL')
    times[label] = float(re.search(r'--- ' + status + ': ' + name + r' \(([0-9.]+)s\)', log)[1])
assert 'expected "insufficient balance", got BuyTicket start' in read(evidence / 'historical-race.txt')
assert 'file exists' in read(evidence / 'historical-corrected-race.txt')
proof = json.loads(read(evidence / 'source-copy-SHA256.json'))
source = workspace / 'tmp/full-state-existing-funds-2026-09-27'
for path, expected in proof.items():
    assert digest(source / path) == expected, path
assert len(proof) == 612
history = json.loads(read(working / 'historical-admission-complete.json'))
assert [int(r['Header']['number'], 16) for r in history] == [15130098, 15130099, 15130111]
assert [r['CanonicalNonce'] for r in history] == [8, 8, 8]
assert [r['PoolStatus'] for r in history] == [0, 2, 2]
assert [r['RemoteAdmissionError'] for r in history] == ['BuyTicket start must be lower than latest block time + 3 hour', '', '']
assert len({r['Saved'] for r in history}) == 1
assert len({r['Transaction'] for r in history}) == 1
retained = [json.loads(read(working / ('diagnostic-saved-' + role + '.json'))) for role in ['producer', 'verifier']]
assert history[0]['Saved'] == retained[0]['Saved']
donation = '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf'
entrant = '0x6813eb9362372eef6200f3b1dbc3f819671cba69'
recipient = json.loads(read(working / 'direct-recipient.json'))
assert recipient['Pending'][donation] == [retained[0]['Transaction']]
result = json.loads(read(working / 'delivery-result.json'))
assert result['Before']['hash'] == retained[0]['Header']['hash'] == retained[1]['Header']['hash']
assert result['Blocks'] == int(result['Final']['number'], 16) - 15130080
assert result['DirectSubmission'] == retained[0]['Transaction']['hash']
assert result['RequiredFreshNonces'] == [9, 27] and not result['NewFunding'] and not result['NonceGapExercised']
assert result['ExactSavedPurchases'] == [r['Transaction'] for r in retained]
assert (working / 'producer-delivery-final.json').read_bytes() == (working / 'verifier-delivery-final.json').read_bytes()
accounts = json.loads(read(working / 'producer-delivery-final.json'))
assert accounts['Accounts'][donation]['Nonce'] >= 10 and accounts['Accounts'][entrant]['Nonce'] >= 28
included = set()
new_purchases = {donation: 0, entrant: 0}
for number in range(1, result['Blocks'] + 1):
    for suffix in ['.json', '.rlp']:
        path = working / 'delivery-blocks' / f'block-{number:02d}{suffix}'
        if number <= 31:
            assert digest(path) == digest(source / 'diagnostic-blocks' / path.name)
        else:
            retain(path, evidence / 'blocks' / path.name)
    if number > 31:
        block = json.loads(read(working / 'delivery-blocks' / f'block-{number:02d}.json'))
        for receipt in block['Receipts']:
            assert receipt['status'] == '0x1'
            included.add(receipt['transactionHash'])
            outcomes = [json.loads(bytes.fromhex(entry['data'][2:])) for entry in receipt['logs']]
            purchases = [outcome for outcome in outcomes if 'TicketOwner' in outcome]
            assert len(purchases) == 1 and not purchases[0].get('Error')
            new_purchases[purchases[0]['TicketOwner']] += 1
assert all(r['Transaction']['hash'] in included for r in retained)
assert new_purchases == {donation: 2, entrant: 7}
trace = [json.loads(line) for line in read(working / 'delivery-pools.jsonl').splitlines()]
assert all(n['Pending'] == {} and n['Queued'] == {} for n in trace[0]['Nodes'])
assert trace[1]['Nodes'][0]['Own']['Saved'] == retained[0]['Saved']
assert trace[1]['Nodes'][0]['Pending'] == {}
assert trace[1]['Nodes'][1]['Pending'][donation] == [retained[0]['Transaction']]
assert any(all(any(int(tx['nonce'], 16) == 9 for tx in node['Pending'].get(donation, [])) for node in observation['Nodes']) for observation in trace)
for name in ['historical-admission-complete.json', 'historical-admission-15130098.json', 'historical-admission-15130099.json', 'historical-admission-15130111.json', 'direct-recipient.json', 'delivery-pools.jsonl', 'delivery-stopped-purchases.json', 'delivery-result.json']:
    retain(working / name, evidence / name)
retain(working / 'producer-delivery-final.json', evidence / 'accounts-final.json')
for role in ['producer', 'verifier']:
    assert digest(working / ('diagnostic-saved-' + role + '.json')) == digest(prior / ('diagnostic-saved-' + role + '.json'))
log = read(evidence / 'live-retained-race.txt')
assert 'exact saved purchase direct delivery and both-owner replenishment passed' in log
assert log.count('--- PASS: TestFullStatePurchaseDirectDelivery') == 5
assert 'participant ledger passed:' in log
assert len(re.findall(r'participant ledger retreat block=', log)) == 2
sources = sorted(set(json.loads(read(prior / 'identities.json'))['sources']) | {'tests/restart/full_state_delivery_linux_test.go', 'tests/restart/continuous_partition_linux_test.go', 'common/fsnparams.go', 'eth/peer.go'})
assert not [p for p in git('diff', '--name-only', baseline).splitlines() if (p.endswith('.go') and not p.endswith('_test.go')) or p in ['go.mod', 'go.sum']]
identities = {'baseline': baseline, 'runtime_changed': False, 'sources': {name: {'git_blob': git('hash-object', '--path=' + name, name), 'sha256': digest(workspace / name)} for name in sources}, 'source_snapshots': {name: digest(evidence / name) for name in ['initial-full_state_delivery_linux_test.go.txt', 'corrected-full_state_delivery_linux_test.go.txt']}, 'build_order': ['initial incorrect funding-error expectation', 'timestamp expectation corrected; immutable output collision retained', 'unique per-height outputs; final source matches retained executable']}
summary = {'seconds': times, 'historical_remote_admission_boundary_passed': True, 'original_wire_rejection_captured': False, 'direct_saved_transaction_included': True, 'both_owner_replenishment_passed': True, 'source_copy_files_unchanged': len(proof), 'canonical_prefix_unchanged_blocks': 31, 'canonical_blocks_audited': result['Blocks'], 'additional_blocks': result['Blocks'] - 31, 'pool_observations': len(trace), 'new_funding': False, 'nonce_gap_exercised': False}
for name, value in [('identities.json', identities), ('results.json', summary)]:
    (evidence / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
print(json.dumps(summary, indent=2))
print(f'{len(sources)} source identities; {len(files)} evidence checksums')
