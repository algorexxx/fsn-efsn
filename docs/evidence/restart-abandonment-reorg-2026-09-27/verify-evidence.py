import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-stale-intent-ordered-2026-09-27'
owner = '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf'
entrant = '0x6813eb9362372eef6200f3b1dbc3f819671cba69'
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
assert identities['ProductionUnchanged'] and identities['SourceFilesUnchanged'] == 605
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
result = read_json(evidence / 'reorg-result.json')
plan = read_json(evidence / 'branch-plan.json')
audit = read_json(evidence / 'cold-audit.json')
assert result['Old'] == plan['Old'] == source['Final']
assert result['Final'] == plan['Remote'] == audit['Heads'][0] == audit['Heads'][1]
assert result['Fork'] == plan['Fork']
assert int(plan['RemoteTD']) > int(plan['OldTD'])
assert result['DownloaderRequested'] and result['HeldDonationSigner']
assert all(result[key] is False for key in ('NewFunding', 'ManualSubmission', 'RecordEdits', 'MiningContinuation'))
assert all(plan[key] is False for key in ('NewFunding', 'HeadRewind', 'RecordEdits'))
assert audit['CommonHead'] and audit['LedgerPassed']
ordinary = decode_rlp((evidence / 'source-results/ordinary-transactions.rlp').read_bytes())
assert len(ordinary) == 34 and int.from_bytes(ordinary[33][0], 'big') == 39
assert ordinary[33][3] == bytes.fromhex(owner[2:]) and not ordinary[33][4] and not ordinary[33][5]
cancel_hash = source['AbandonmentReceipt']['transactionHash']
count = int(result['Final']['number'], 16)-15130080
fork = int(plan['Fork']['number'], 16)-15130080
assert fork == 52
canonical, displaced = {}, {}
for label, blocks in (('old-branch', 60), ('competing-branch', count), ('audit-producer', count), ('audit-verifier', count)):
    assert len(list((evidence / label).iterdir())) == blocks * 2
    last = None
    for number in range(1, blocks+1):
        entry = read_json(evidence / label / f'block-{number:02d}.json')
        header = entry['Header']
        assert int(header['number'], 16) == 15130080+number
        if last:
            assert header['parentHash'] == last
        last = header['hash']
        encoded = (evidence / label / f'block-{number:02d}.rlp').read_bytes()
        block = decode_rlp(encoded)
        fields = block[0]
        for index, key in ((0, 'parentHash'), (2, 'miner'), (3, 'stateRoot'), (4, 'transactionsRoot'), (5, 'receiptsRoot'), (13, 'mixHash')):
            assert fields[index] == bytes.fromhex(header[key][2:])
        for index, key in ((7, 'difficulty'), (8, 'number'), (9, 'gasLimit'), (10, 'gasUsed'), (11, 'timestamp')):
            assert int.from_bytes(fields[index], 'big') == int(header[key], 16)
        assert len(block[1]) == len(entry['Receipts'])
        for extension in ('json', 'rlp'):
            name = f'block-{number:02d}.{extension}'
            reference = previous / 'audit-producer' / name if label == 'old-branch' or number <= fork else evidence / 'competing-branch' / name
            assert digest(evidence / label / name) == digest(reference)
        for index, (tx, receipt) in enumerate(zip(block[1], entry['Receipts'])):
            assert receipt['status'] == '0x1' and receipt['blockHash'] == header['hash']
            assert int(receipt['blockNumber'], 16) == 15130080+number and int(receipt['transactionIndex'], 16) == index
            if label == 'old-branch' and number > fork:
                if receipt['transactionHash'] == cancel_hash or receipt['transactionHash'] in [purchase['hash'] for purchase in source['FreshPurchases']]:
                    nonce = int.from_bytes(tx[0], 'big')
                    displaced[nonce] = {'Hash': receipt['transactionHash'], 'Fields': tx, 'Block': header['hash'], 'Height': 15130080+number, 'Index': index}
            if label == 'audit-producer':
                canonical[receipt['transactionHash']] = receipt
            if label != 'old-branch' and number > fork:
                assert header['miner'] == entrant and len(block[1]) == 1
                assert tx[3] == bytes.fromhex('ff'*20) and not tx[4]
                assert int.from_bytes(decode_rlp(tx[5])[0], 'big') == 4
                native = [json.loads(bytes.fromhex(log['data'][2:])) for log in receipt['logs'] if log['topics'] == ['0x'+'0'*63+'4']]
                assert len(native) == 1 and 'Error' not in native[0]
                assert native[0]['TicketOwner'].lower() == entrant
                ticket = entry['Tickets'][native[0]['TicketID']]
                assert ticket['Owner'] == entrant and ticket['Height'] == 15130080+number
    assert last == (result['Old'] if label == 'old-branch' else result['Final'])['hash']
assert sorted(displaced) == [39, 40, 41, 42]
assert displaced[39]['Fields'] == ordinary[33]
for purchase in source['FreshPurchases']:
    check_transaction(displaced[int(purchase['nonce'], 16)]['Fields'], purchase)
assert all(value['Hash'] not in canonical for value in displaced.values())
assert source['Stale']['hash'] not in canonical
assert result['Before']['Nonce'] == 43 and result['Before']['Saved'] == source_intents[0]['Saved']
assert len(result['Before']['Pending']) == 1 and not result['Before']['Queued']
saved = decode_rlp(bytes.fromhex(source_intents[0]['Saved'][2:]))
check_transaction(saved, result['Before']['Pending'][0])
assert int.from_bytes(saved[0], 'big') == 43
for label, empty in (('live-rollback', False), ('cold-rollback', True)):
    rows = read_json(evidence / f'{label}.json')
    assert len(rows) >= 10
    for row in rows:
        node, purchase = row['Node'], row['Purchase']
        assert node['Hash'] == node['Full'] == node['Header'] == node['Fast'] == result['Final']['hash']
        assert node['Mining'] and node['AutoBuy'] and node['Signatures'] == 0
        assert purchase['Nonce'] == 39 and purchase['Saved'] == source_intents[0]['Saved'] and not purchase['Queued']
        assert len(purchase['Pending'] or []) == (0 if empty else 2)
        if not empty:
            for nonce, tx in zip((39, 40), purchase['Pending']):
                assert tx['hash'] == displaced[nonce]['Hash']
                check_transaction(displaced[nonce]['Fields'], tx)
        assert len(row['Recovered']) == 4
        for recovered in row['Recovered']:
            expected = displaced[recovered['Nonce']]
            assert all(recovered[key] == expected[key] for key in ('Hash', 'Block', 'Height', 'Index'))
            assert decode_rlp(bytes.fromhex(recovered['Raw'][2:])) == expected['Fields'] and recovered['Receipt'] is None
    assert rows[-1]['Purchase'] == result['Cold' if empty else 'Live']
for i, role in enumerate(('producer', 'verifier')):
    inventory = read_json(evidence / f'cold-{role}.json')
    assert inventory['Header'] == result['Final']
    assert inventory['Accounts'] == read_json(evidence / 'preflight-verifier.json')['Accounts']
    assert inventory['Tickets'] == read_json(evidence / 'preflight-verifier.json')['Tickets']
    assert inventory['Accounts'][owner]['Nonce'] == 39 and inventory['Accounts'][owner]['TicketCount'] == 0
    assert inventory['Accounts'][owner]['LiquidWei'] == '5021976763487999978776'
    assert inventory['Accounts'][backup] == read_json(evidence / 'preflight-producer.json')['Accounts'][backup]
    entries = audit['AdditionalFunding'][i]
    assert len(entries) == 33 and cancel_hash not in entries
    before = read_json(evidence / 'source-results/cold-audit.json')['AdditionalFunding'][i]
    assert entries == {tx: height for tx, height in before.items() if tx != cancel_hash}
cold = read_json(evidence / 'cold-intents-producer.json')[0]
assert cold['Nonce'] == 39 and cold['Saved'] == source_intents[0]['Saved']
check_transaction(saved, cold['Transaction'])
log = (evidence / 'live-race.txt').read_text(encoding='utf-8')
assert 'another ticket purchase' in log and 'needs nonce 43, current nonce is 39' in log
assert 'Chain split detected' in log
assert 'Served lab_sync' in log
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
print(json.dumps({'EvidenceFiles': len(lines), 'SavedNonce': 43, 'RolledBackNonce': 39,
                  'CanonicalLedgerBlocksPerNode': count, 'OldLedgerBlocks': 60,
                  'CommonPrefixBlocks': fork, 'CanonicalAbandonmentAbsent': True,
                  'DisplacedRawBytesRetainedBeforeAndAfterRestart': 4,
                  'FinalHead': result['Final']['hash']}, indent=2))


