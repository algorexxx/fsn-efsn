import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-stale-intent-ordered-2026-09-27'
owners = ['0x2b5ad5c4795c026514f8317c7a215e218dccd6cf', '0x6813eb9362372eef6200f3b1dbc3f819671cba69']
backup = '0x7e5f4552091a69125d5dfcb7b8c2659029395bdf'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def decode_rlp(data):
    def item(offset):
        tag = data[offset]
        if tag < 128:
            return data[offset:offset + 1], offset + 1
        is_list = tag >= 192
        short = 192 if is_list else 128
        long = short + 55
        if tag <= long:
            start, length = offset + 1, tag - short
        else:
            width = tag - long
            start = offset + 1 + width
            length = int.from_bytes(data[offset + 1:start], 'big')
        end = start + length
        assert end <= len(data)
        if not is_list:
            return data[start:end], end
        children = []
        while start < end:
            child, start = item(start)
            children.append(child)
        assert start == end
        return children, end
    value, end = item(0)
    assert end == len(data)
    return value


def check_transaction(fields, tx):
    assert len(fields) == 9
    for index, key in ((0, 'nonce'), (1, 'gasPrice'), (2, 'gas'), (4, 'value'), (6, 'v'), (7, 'r'), (8, 's')):
        assert int.from_bytes(fields[index], 'big') == int(tx[key], 16)
    assert fields[3] == bytes.fromhex(tx['to'][2:]) and fields[5] == bytes.fromhex(tx['input'][2:])


identities = read_json(evidence / 'identities.json')
assert identities['ProductionUnchanged'] and identities['SourceFilesUnchanged'] == 606
assert identities['LiveExit'] == identities['ColdExit'] == 0
for phase in ('live', 'cold'):
    log = (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in log and '--- FAIL:' not in log
    assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == 0
for name in ('test-sources.sha256', 'production-sources.sha256'):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
source = read_json(evidence / 'source-results/stale-recovery-result.json')
source_intents = read_json(evidence / 'source-results/stopped-purchases.json')
result = read_json(evidence / 'restart-result.json')
audit = read_json(evidence / 'cold-audit.json')
assert result['Before'] == source['Final']
assert result['StaleHash'] == source['Stale']['hash']
assert all(result[key] is False for key in ('NewFunding', 'ManualSubmission', 'RecordEdits', 'StaleInjection'))
assert audit['CommonHead'] and audit['LedgerPassed']
assert result['Final'] == audit['Heads'][0] == audit['Heads'][1]
assert audit['AdditionalFunding'] == read_json(evidence / 'source-results/cold-audit.json')['AdditionalFunding']
assert all(len(entries) == 34 for entries in audit['AdditionalFunding'])
restored = read_json(evidence / 'restored-purchase.json')
assert restored['Raw'] == source_intents[0]['Saved']
saved = decode_rlp(bytes.fromhex(restored['Raw'][2:]))
check_transaction(saved, restored['Transaction'])
assert restored['Transaction']['hash'] == '0xddb72dc7336546fdbe48be0570dca20587a77c51aa5e61d3664d468e7f04097a'
assert int(restored['Transaction']['nonce'], 16) == 43 and restored['StableSeconds'] == 6
for i, initial in enumerate(restored['Initial']):
    assert initial['Nonce'] == source_intents[i]['Nonce'] and initial['Saved'] == source_intents[i]['Saved']
    assert not initial['Pending'] and not initial['Queued']
for phase in ('Restored', 'AfterRetryWindow'):
    purchase = restored[phase]
    assert purchase['Nonce'] == 43 and purchase['Saved'] == restored['Raw']
    assert purchase['Pending'] == [restored['Transaction']] and not purchase['Queued']
for i, status in enumerate(restored['Nodes']):
    assert status['Number'] == 15130140
    assert status['Hash'] == status['Full'] == status['Fast'] == status['Header'] == result['Before']['hash']
    assert status['Mining'] == status['AutoBuy'] == (i == 0)
count = int(result['Final']['number'], 16)-15130080
live_height = int(result['Live']['number'], 16)
canonical = {}
transactions = {}
new_nonces = {owner: [] for owner in owners}
produced = {owner: 0 for owner in owners}
for i, role in enumerate(('producer', 'verifier')):
    assert digest(evidence / f'preflight-{role}.json') == digest(previous / f'cold-{role}.json')
    inventory = read_json(evidence / f'cold-{role}.json')
    assert inventory['Header'] == result['Final']
    assert inventory['Accounts'][backup] == read_json(previous / f'cold-{role}.json')['Accounts'][backup]
    assert len(list((evidence / f'audit-{role}').iterdir())) == count*2
    last = None
    for number in range(1, count+1):
        for suffix in ('json', 'rlp'):
            name = f'block-{number:02d}.{suffix}'
            path = evidence / f'audit-{role}' / name
            assert digest(path) == digest(evidence / 'audit-producer' / name)
            if number <= 60:
                assert digest(path) == digest(previous / f'audit-{role}' / name)
        block = read_json(evidence / f'audit-{role}' / f'block-{number:02d}.json')
        header = block['Header']
        assert int(header['number'], 16) == 15130080+number
        if last is not None:
            assert header['parentHash'] == last
        last = header['hash']
        fields = decode_rlp((evidence / f'audit-{role}' / f'block-{number:02d}.rlp').read_bytes())
        assert len(fields[1]) == len(block['Receipts'])
        if number > 60:
            assert header['miner'] in owners
            if i == 0 and int(header['number'], 16) <= live_height:
                produced[header['miner']] += 1
        for raw_tx, receipt in zip(fields[1], block['Receipts']):
            assert receipt['status'] == '0x1' and receipt['blockHash'] == last
            assert int(receipt['blockNumber'], 16) == int(header['number'], 16)
            canonical[receipt['transactionHash']] = receipt
            transactions[receipt['transactionHash']] = raw_tx
            if number > 60:
                assert raw_tx[3] == bytes.fromhex('ff'*20) and int.from_bytes(raw_tx[4], 'big') == 0
                assert int.from_bytes(decode_rlp(raw_tx[5])[0], 'big') == 4
                native = [json.loads(bytes.fromhex(log['data'][2:])) for log in receipt['logs'] if log['topics'] == ['0x'+'0'*63+'4']]
                assert len(native) == 1 and 'Error' not in native[0]
                owner = native[0]['TicketOwner'].lower()
                assert owner in owners
                ticket = block['Tickets'][native[0]['TicketID']]
                assert ticket['Owner'] == owner and ticket['Height'] == 15130080+number
                if i == 0:
                    new_nonces[owner].append(int.from_bytes(raw_tx[0], 'big'))
    assert last == result['Final']['hash']
assert result['StaleHash'] not in canonical
assert result['ProducedThroughLive'] == [produced[owner] for owner in owners] and all(produced.values())
inclusion = read_json(evidence / 'saved-inclusion.json')
assert inclusion['Transaction'] == restored['Transaction'] and inclusion['Header'] == result['SavedInclusion']
receipt = canonical[restored['Transaction']['hash']]
assert receipt['blockHash'] == inclusion['Header']['hash']
assert transactions[restored['Transaction']['hash']] == saved
stopped = read_json(evidence / 'stopped-purchases.json')
for i, owner in enumerate(owners):
    assert len(result['Purchases'][i]) >= 3
    assert new_nonces[owner] == list(range(source_intents[i]['Nonce'], source_intents[i]['Nonce']+len(new_nonces[owner])))
    for nonce, tx in enumerate(result['Purchases'][i], source_intents[i]['Nonce']):
        assert int(tx['nonce'], 16) == nonce and tx['hash'] in canonical
        check_transaction(transactions[tx['hash']], tx)
    cold = read_json(evidence / f'cold-intents-{("producer", "verifier")[i]}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] and cold['Saved'] == stopped[i]['Saved']
    assert cold['Nonce'] == source_intents[i]['Nonce']+len(new_nonces[owner])
    assert cold['Saved'] != restored['Raw']
assert result['Purchases'][0][0] == restored['Transaction']
progress = [json.loads(line) for line in (evidence / 'progress.jsonl').read_text(encoding='utf-8').splitlines()]
assert progress
for sample in progress:
    for node in sample['Nodes']:
        assert node['Mining'] and node['AutoBuy']
if '--refresh' in sys.argv:
    files = sorted(path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS')
    (evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
lines = (evidence / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
for line in lines:
    expected, relative = line.split('  ', 1)
    assert digest(evidence / relative) == expected, relative
    if '--index' in sys.argv:
        data = subprocess.check_output(['git', 'show', ':' + (evidence / relative).relative_to(workspace).as_posix()], cwd=workspace)
        assert hashlib.sha256(data).hexdigest() == expected, relative
assert len(lines) == len([path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS'])
print(json.dumps({'EvidenceFiles': len(lines), 'SavedPurchaseIncludedUnchanged': True,
                  'ColdLedgerBlocksPerNode': count, 'OriginalPrefixArtifactsUnchanged': 240,
                  'NewPurchaseNonces': new_nonces, 'ProducedThroughLive': produced,
                  'FinalHead': result['Final']['hash']}, indent=2))


