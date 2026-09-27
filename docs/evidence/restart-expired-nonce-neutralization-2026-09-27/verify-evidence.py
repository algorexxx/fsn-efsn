import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-equal-weight-pause-2026-09-27'


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
assert identities['ProductionUnchanged'] and identities['SourceFilesUnchanged'] == 596
assert identities['LiveExit'] == identities['ColdExit'] == 0
for phase in ('live', 'cold'):
    log = (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in log and '--- FAIL:' not in log
    assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == 0
for name in ('test-sources.sha256', 'production-sources.sha256'):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
source = read_json(evidence / 'source-results/pause-result.json')
result = read_json(evidence / 'neutralization-result.json')
audit = read_json(evidence / 'cold-audit.json')
assert audit['CommonHead'] and audit['LedgerPassed']
assert result['Final'] == audit['Heads'][0] == audit['Heads'][1]
assert result['Before'] == read_json(evidence / 'source-results/cold-audit.json')['Heads'][0]
assert result['NonceBefore'] == 8 and result['NonceAfter'] == 39
assert result['Saved'] == source['Stopped']['Purchases'][0]['Saved']
assert all(result[key] is False for key in ('NewFunding', 'AutomaticReplacement', 'PurchasesRestored', 'ExpiredProbeWasHistoricalOriginal'))
owner = '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf'
transfers = read_json(evidence / 'neutralizations.json')
encoded = decode_rlp((evidence / 'neutralizations.rlp').read_bytes())
assert len(transfers) == len(encoded) == 31
assert len({tx['hash'] for tx in transfers}) == 31
pool = read_json(evidence / 'recipient-before-mining.json')
assert pool['Pending'][owner] == transfers and not pool['Queued'].get(owner)
assert audit['AdditionalFunding'][0] == audit['AdditionalFunding'][1]
assert set(audit['AdditionalFunding'][0]) == {tx['hash'] for tx in transfers}
for i, (fields, tx) in enumerate(zip(encoded, transfers)):
    check_transaction(fields, tx)
    assert int(tx['nonce'], 16) == i + 8 and tx['to'] == owner
    assert int(tx['gasPrice'], 16) == 2_000_000_000 and int(tx['gas'], 16) == 21000
    assert tx['value'] == '0x0' and tx['input'] == '0x'
    height = audit['AdditionalFunding'][0][tx['hash']]
    assert height == 15130127
    block_fields = decode_rlp((evidence / 'audit-producer' / f'block-{height-15130080:02d}.rlp').read_bytes())
    assert block_fields[1].count(fields) == 1
    for receipts in result['Receipts']:
        receipt = receipts[i]
        assert receipt['transactionHash'] == tx['hash'] and receipt['status'] == '0x1'
        assert int(receipt['gasUsed'], 16) == 21000 and not receipt['logs']
        assert int(receipt['blockNumber'], 16) == height
        block = read_json(evidence / 'audit-producer' / f'block-{height-15130080:02d}.json')
        assert receipt['blockHash'] == block['Header']['hash'] and receipt in block['Receipts']
assert result['Receipts'][0] == result['Receipts'][1]
probe = read_json(evidence / 'expired-probe.json')
check_transaction(decode_rlp(bytes.fromhex(probe['Raw'][2:])), probe['Transaction'])
assert probe['HistoricalOriginal'] is False and probe['SavedIntentChanged'] is False
assert probe['Head'] == result['Before']
head_time = int(probe['Head']['timestamp'], 16)
assert probe['Purchase'] == {'Start': head_time-2*86400, 'End': head_time+28*86400}
assert probe['PoolError'] == 'BuyTicket end must be greater than latest block time + 1 month'
assert probe['Transaction']['hash'] not in audit['AdditionalFunding'][0]
assert len(result['BuyerSamples']) >= 10
for sample in result['BuyerSamples']:
    purchase, node = sample['Purchase'], sample['Node']
    assert purchase['Nonce'] == 39 and purchase['Saved'] == result['Saved']
    assert not purchase['Pending'] and not purchase['Queued']
    assert node['Mining'] and node['AutoBuy']
assert 'insufficient balance(2021976763487999978776)' in (evidence / 'live-race.txt').read_text(encoding='utf-8')
fee = 31 * 21000 * 2_000_000_000
stopped = read_json(evidence / 'stopped-purchases.json')
height = int(result['Final']['number'], 16)
assert height == 15130130
for i, role in enumerate(('producer', 'verifier')):
    inventory = read_json(evidence / f'cold-{role}.json')
    initial = read_json(previous / f'cold-{role}.json')['Accounts'][owner]
    final = inventory['Accounts'][owner]
    assert final['Nonce'] == 39 and final['TicketCount'] == 0
    assert int(initial['LiquidWei']) - int(final['LiquidWei']) == fee
    assert final['TimeLocks'] == initial['TimeLocks']
    cold = read_json(evidence / f'cold-intents-{role}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] and cold['Saved'] == stopped[i]['Saved']
    assert not stopped[i]['Pending'] and not stopped[i]['Queued']
    if i == 0:
        assert cold['Saved'] == result['Saved']
    else:
        assert cold['Nonce'] == 44
    assert inventory['Header'] == result['Final']
    files = list((evidence / f'audit-{role}').iterdir())
    assert len(files) == 2 * (height - 15130080)
    last = None
    for number in range(1, height - 15130080 + 1):
        for suffix in ('json', 'rlp'):
            name = f'block-{number:02d}.{suffix}'
            path = evidence / f'audit-{role}' / name
            assert digest(path) == digest(evidence / 'audit-producer' / name)
            if number <= 46:
                assert digest(path) == digest(previous / f'audit-{role}' / name)
        block = read_json(evidence / f'audit-{role}' / f'block-{number:02d}.json')
        assert int(block['Header']['number'], 16) == 15130080 + number
        if last is not None:
            assert block['Header']['parentHash'] == last
        last = block['Header']['hash']
        if number > 46:
            assert block['Header']['miner'] == '0x6813eb9362372eef6200f3b1dbc3f819671cba69'
        for receipt in block['Receipts']:
            assert receipt['status'] == '0x1' and receipt['blockHash'] == last
    assert last == result['Final']['hash']
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
print(json.dumps({'EvidenceFiles': len(lines), 'Neutralizations': 31, 'TotalGasCostWei': str(fee),
                  'NonceBefore': 8, 'NonceAfter': 39, 'SavedIntentUnchanged': True,
                  'ColdLedgerBlocksPerNode': height-15130080, 'HistoricalPrefixArtifactsUnchanged': 184,
                  'FinalHead': result['Final']['hash']}, indent=2))
