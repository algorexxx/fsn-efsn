import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


for phase in ('live', 'cold'):
    assert 'WARNING: DATA RACE' not in (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
assert (evidence / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
first = evidence / 'attempt-01'
assert (first / 'live-exit.txt').read_text(encoding='utf-8').strip() == '1'
assert (first / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
assert read_json(first / 'before-outage.json')['Ready'] is False
for line in (first / 'test-sources.sha256').read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ', 1)
    retained = first / (Path(relative).name + '.txt')
    assert digest(retained if retained.exists() else workspace / relative) == expected, relative
second = evidence / 'attempt-02'
assert (second / 'live-exit.txt').read_text(encoding='utf-8').strip() == '1'
assert (second / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
assert all(int(head['number'], 16) == 15130090 for head in read_json(second / 'cold-audit.json')['Heads'])
for attempt in (first, second):
    for phase in ('live', 'cold'):
        assert 'WARNING: DATA RACE' not in (attempt / f'{phase}-race.txt').read_text(encoding='utf-8')
result_path = evidence / 'repair-result.json'
result = read_json(result_path) if result_path.exists() else None
repair = evidence / 'repair'
direct = 0
confirmed = []
for path in sorted(repair.glob('delivery-*.jsonl')):
    suffix = path.stem.removeprefix('delivery-')
    if not suffix.isdigit():
        continue
    nonce = int(suffix)
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    for index, record in enumerate(records):
        if record['Stage'] == 'before-direct-delivery':
            assert record['Bytes'] == '0x' + (repair / f'original-{nonce}.rlp').read_bytes().hex()
            target = record['Target']
            origin = record['Nodes'][1 - target]
            recipient = record['Nodes'][target]
            assert origin['Header']['hash'] == recipient['Header']['hash']
            assert origin['Own']['Nonce'] == nonce
            assert origin['Own']['Saved'] == '0x' + (repair / 'saved.rlp').read_bytes().hex()
            assert len(origin['Own']['Pending']) == 1
            assert origin['Own']['Pending'][0]['hash'] == record['Transaction']
            sender = read_json(evidence / 'funding-plan.json')['Recipient']
            assert not recipient['Pending'].get(sender) and not recipient['Queued'].get(sender)
            response = records[index + 1]
            assert response['Stage'] == 'direct-delivery-result'
            if not response['RPCError']:
                assert response['Submitted'] == record['Transaction']
                direct += 1
        if record['Stage'] == 'canonical-native-success':
            number = int(record['Block']['number'], 16) - 15130080
            block = read_json(evidence / 'blocks-producer' / f'block-{number:02d}.json')
            assert block['Header']['hash'] == record['Block']['hash']
            receipt = next(item for item in block['Receipts'] if item['transactionHash'] == record['Transaction'])
            assert receipt['status'] == '0x1'
            native = [json.loads(bytes.fromhex(item['data'][2:])) for item in receipt['logs']
                      if item['address'] == '0xffffffffffffffffffffffffffffffffffffffff'
                      and item['topics'][0] == '0x' + '04'.rjust(64, '0')]
            assert any(not item.get('Error') and 'TicketID' in item for item in native)
            confirmed.append((nonce, record['Transaction'], int(record['Block']['number'], 16), record['DirectDelivery']))

if (evidence / 'live-exit.txt').read_text(encoding='utf-8').strip() == '0':
    assert result['FundingFailure'] == '' and result['Successors'] >= 2
    assert sorted(item[0] for item in confirmed) == list(range(result['CanonicalNonce'], result['SavedNonce'] + 1))
    saved = next(item for item in confirmed if item[0] == result['SavedNonce'])
    assert saved[1] == result['SavedHash'] and saved[3] is False
    stopped = read_json(evidence / 'stopped-purchases.json')
    for index, role in enumerate(('producer', 'verifier')):
        cold = read_json(evidence / f'cold-intents-{role}.json')[index]
        assert cold['Nonce'] == stopped[index]['Nonce'] and cold['Saved'] == stopped[index]['Saved']

for line in (evidence / 'test-sources.sha256').read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ', 1)
    assert digest(workspace / relative) == expected, relative
if '--refresh' in sys.argv:
    files = sorted(p for p in evidence.rglob('*') if p.is_file() and p != evidence / 'SHA256SUMS')
    (evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
lines = (evidence / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
for line in lines:
    expected, relative = line.split('  ', 1)
    assert digest(evidence / relative) == expected, relative
    if '--index' in sys.argv:
        blob = subprocess.check_output(['git', 'show', ':' + (evidence / relative).relative_to(workspace).as_posix()], cwd=workspace)
        assert hashlib.sha256(blob).hexdigest() == expected, relative
print(json.dumps({'EvidenceFiles': len(lines), 'SuccessfulDirectSubmissions': direct, 'ConfirmedPurchases': confirmed}, indent=2))
