import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


for phase in ('live', 'cold'):
    assert (evidence / f'{phase}-exit.txt').read_text(encoding='utf-8').strip() == '0', phase
    assert 'WARNING: DATA RACE' not in (evidence / f'{phase}-race.txt').read_text(encoding='utf-8'), phase
for line in (evidence / 'test-sources.sha256').read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ', 1)
    assert digest(workspace / relative) == expected, relative
result = read_json(evidence / 'repair-result.json')
assert result['FundingFailure'] == '' and result['Successors'] >= 2
assert result['OriginalsIncluded'] == result['SavedNonce'] - result['CanonicalNonce']
assert len(result['Funding']) == 2
assert read_json(evidence / 'before-outage.json')['Ready'] is True
repair = evidence / 'repair'
injection = [json.loads(line) for line in (repair / 'injected-rejection.jsonl').read_text(encoding='utf-8').splitlines()]
assert [row['Stage'] for row in injection] == ['before-price-injection', 'price-raised',
    'remote-rejection-observed', 'normal-price-restored', 'still-stranded-after-price-restore']
target = injection[0]['Recipient']
owner = result['Owner']
tx_hash = injection[0]['Transaction']
normal = injection[0]['Detail']['Normal']
raised = injection[0]['Detail']['Raised']
assert injection[1]['Detail'] == raised and injection[3]['Detail'] == normal
for row in injection:
    assert row['Transaction'] == tx_hash and row['Recipient'] == target
for row in injection[2:]:
    origin = row['Nodes'][1 - target]
    recipient = row['Nodes'][target]
    assert origin['Own']['Nonce'] == result['CanonicalNonce']
    assert origin['Own']['Saved'] == '0x' + (repair / 'saved.rlp').read_bytes().hex()
    pending = origin['Pending'][owner]
    assert len(pending) == 1 and pending[0]['hash'] == tx_hash
    assert int(raised, 16) == int(pending[0]['gasPrice'], 16) + 1
    assert int(normal, 16) <= int(pending[0]['gasPrice'], 16)
    assert not recipient['Pending'].get(owner) and not recipient['Queued'].get(owner)
rejection = injection[2]['Detail']
assert rejection['msg'] == 'Discarding invalid transaction'
assert rejection['hash'] == tx_hash and rejection['err'] == 'transaction underpriced'
native = []
for line in (evidence / 'live-race.txt').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line.startswith('{'):
        native.append(json.loads(line))
assert rejection in native
restored = datetime.fromisoformat(injection[3]['ObservedUTC'])
stranded = datetime.fromisoformat(injection[4]['ObservedUTC'])
assert (stranded - restored).total_seconds() >= 15
confirmed = []
direct = []
for path in sorted(repair.glob('delivery-*.jsonl')):
    suffix = path.stem.removeprefix('delivery-')
    if not suffix.isdigit():
        continue
    nonce = int(suffix)
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    for index, row in enumerate(rows):
        if row['Stage'] == 'before-direct-delivery':
            assert nonce < result['SavedNonce']
            assert row['Bytes'] == '0x' + (repair / f'original-{nonce}.rlp').read_bytes().hex()
            origin, recipient = row['Nodes'][1 - row['Target']], row['Nodes'][row['Target']]
            assert origin['Header']['hash'] == recipient['Header']['hash']
            assert origin['Own']['Nonce'] == nonce
            assert origin['Own']['Saved'] == '0x' + (repair / 'saved.rlp').read_bytes().hex()
            assert len(origin['Pending'][owner]) == 1 and origin['Pending'][owner][0]['hash'] == row['Transaction']
            assert not recipient['Pending'].get(owner) and not recipient['Queued'].get(owner)
            response = rows[index + 1]
            assert response['Stage'] == 'direct-delivery-result'
            if not response['RPCError']:
                assert response['Submitted'] == row['Transaction']
                direct.append(row['Transaction'])
            if row['Transaction'] == tx_hash:
                assert datetime.fromisoformat(row['ObservedUTC']) > stranded
        if row['Stage'] == 'canonical-native-success':
            number = int(row['Block']['number'], 16) - 15130080
            block = read_json(evidence / 'blocks-producer' / f'block-{number:02d}.json')
            assert block['Header'] == row['Block']
            receipt = next(item for item in block['Receipts'] if item['transactionHash'] == row['Transaction'])
            assert receipt['status'] == '0x1'
            native_logs = [json.loads(bytes.fromhex(item['data'][2:])) for item in receipt['logs']
                           if item['address'] == '0xffffffffffffffffffffffffffffffffffffffff'
                           and item['topics'][0] == '0x' + '04'.rjust(64, '0')]
            assert any(not item.get('Error') and item.get('TicketOwner') == owner and 'TicketID' in item for item in native_logs)
            confirmed.append((nonce, row['Transaction'], int(row['Block']['number'], 16), row['DirectDelivery']))
assert tx_hash in direct
assert sorted(row[0] for row in confirmed) == list(range(result['CanonicalNonce'], result['SavedNonce'] + 1))
assert next(row for row in confirmed if row[0] == result['CanonicalNonce'])[1::2] == (tx_hash, True)
saved = next(row for row in confirmed if row[0] == result['SavedNonce'])
assert saved[1] == result['SavedHash'] and saved[3] is False
audit = read_json(evidence / 'cold-audit.json')
assert audit['CommonHead'] and audit['Heads'][0] == audit['Heads'][1]
assert audit['Heads'][0]['hash'] == result['Final']
assert audit['AdditionalFunding'] == [result['Funding'], result['Funding']]
stopped = read_json(evidence / 'stopped-purchases.json')
for index, role in enumerate(('producer', 'verifier')):
    cold = read_json(evidence / f'cold-intents-{role}.json')[index]
    assert cold['Nonce'] == stopped[index]['Nonce'] and cold['Saved'] == stopped[index]['Saved']
if '--refresh' in sys.argv:
    files = sorted(p for p in evidence.rglob('*') if p.is_file() and p != evidence / 'SHA256SUMS')
    (evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
lines = (evidence / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
for line in lines:
    expected, relative = line.split('  ', 1)
    assert digest(evidence / relative) == expected, relative
    if '--index' in sys.argv:
        data = subprocess.check_output(['git', 'show', ':' + (evidence / relative).relative_to(workspace).as_posix()], cwd=workspace)
        assert hashlib.sha256(data).hexdigest() == expected, relative
print(json.dumps({'EvidenceFiles': len(lines), 'InjectedTransaction': tx_hash,
                  'StrandedAfterRestoreSeconds': (stranded - restored).total_seconds(),
                  'DirectSubmissions': direct, 'ConfirmedPurchases': sorted(confirmed)}, indent=2))
