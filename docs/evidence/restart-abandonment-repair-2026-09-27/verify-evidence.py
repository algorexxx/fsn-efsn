import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
previous = evidence.parent / 'restart-abandonment-reorg-2026-09-27'
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
assert identities['ProductionUnchanged'] and identities['SourceFilesUnchanged'] == 618
assert identities['LiveExit'] == identities['ColdExit'] == 0
for phase in ('live', 'cold'):
    log = (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in log and '--- FAIL:' not in log
    assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == 0
for name in ('test-sources.sha256', 'production-sources.sha256'):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
prior = read_json(evidence / 'source-results/reorg-result.json')
source = read_json(evidence / 'source-results/stale-recovery-result.json')
result = read_json(evidence / 'repair-result.json')
audit = read_json(evidence / 'cold-audit.json')
assert result['Before'] == prior['Final']
assert result['Final'] == audit['Heads'][0] == audit['Heads'][1]
assert all(result[key] is False for key in ('NewFunding', 'RecordEdits', 'ResignedOriginals', 'HeldSigner'))
assert audit['CommonHead'] and audit['LedgerPassed']
assert result['Repair']['OriginalsIncluded'] == 3 and result['Repair']['Successors'] >= 2
assert not result['Repair']['FundingFailure'] and not result['Repair']['Funding']
assert result['Repair']['CanonicalNonce'] == 40 and result['Repair']['SavedNonce'] == 43
cancel = read_json(evidence / 'abandonment-replayed.json')
assert cancel['Transaction'] == result['Abandonment']
assert cancel['Receipt'] == result['AbandonmentReceipt']
cancel_hash = cancel['Transaction']['hash']
assert cancel_hash == source['AbandonmentReceipt']['transactionHash']
assert cancel['Receipt']['blockHash'] != source['AbandonmentReceipt']['blockHash']
assert int(cancel['Receipt']['blockNumber'], 16) > int(result['Before']['number'], 16)
assert cancel['After']['Nonce'] == 40 and cancel['After']['Saved'] == prior['Cold']['Saved']
assert not cancel['After']['Pending'] and not cancel['After']['Queued']
assert not cancel['Receipt']['logs'] and int(cancel['Receipt']['gasUsed'], 16) == 21000
originals = {int(tx['nonce'], 16): tx for tx in source['FreshPurchases']}
originals[39] = cancel['Transaction']
old_locations = {}
for number in range(53, 61):
    path = evidence / 'source-results/old-branch' / f'block-{number:02d}.rlp'
    assert digest(path) == digest(previous / 'old-branch' / path.name)
    block = decode_rlp(path.read_bytes())
    entry = read_json(previous / 'old-branch' / f'block-{number:02d}.json')
    for fields, receipt in zip(block[1], entry['Receipts']):
        for nonce, tx in originals.items():
            if receipt['transactionHash'] == tx['hash']:
                check_transaction(fields, tx)
                raw = bytes.fromhex(cancel['Raw'][2:]) if nonce == 39 else (evidence / 'repair' / f'original-{nonce}.rlp').read_bytes()
                assert decode_rlp(raw) == fields
                old_locations[nonce] = receipt['blockHash']
assert sorted(old_locations) == [39, 40, 41, 42]
saved_raw = (evidence / 'repair/saved.rlp').read_bytes()
assert saved_raw == bytes.fromhex(prior['Cold']['Saved'][2:])
saved_fields = decode_rlp(saved_raw)
saved_hash = result['Repair']['SavedHash']
count = int(result['Final']['number'], 16)-15130080
live_height = int(result['Live']['number'], 16)
canonical, transactions = {}, {}
new_nonces = {owner: [] for owner in owners}
produced = {owner: 0 for owner in owners}
for i, role in enumerate(('producer', 'verifier')):
    assert digest(evidence / f'preflight-{role}.json') == digest(previous / f'cold-{role}.json')
    inventory = read_json(evidence / f'cold-{role}.json')
    assert inventory['Header'] == result['Final']
    assert inventory['Accounts'][backup] == read_json(previous / f'cold-{role}.json')['Accounts'][backup]
    assert len(list((evidence / f'audit-{role}').iterdir())) == count * 2
    last = None
    for number in range(1, count+1):
        for suffix in ('json', 'rlp'):
            name = f'block-{number:02d}.{suffix}'
            path = evidence / f'audit-{role}' / name
            assert digest(path) == digest(evidence / 'audit-producer' / name)
            if number <= 68:
                assert digest(path) == digest(previous / f'audit-{role}' / name)
        entry = read_json(evidence / f'audit-{role}' / f'block-{number:02d}.json')
        header = entry['Header']
        assert int(header['number'], 16) == 15130080+number
        if last:
            assert header['parentHash'] == last
        last = header['hash']
        block = decode_rlp((evidence / f'audit-{role}' / f'block-{number:02d}.rlp').read_bytes())
        assert len(block[1]) == len(entry['Receipts'])
        if number > 68:
            assert header['miner'] in owners
            if i == 0 and 15130080+number <= live_height:
                produced[header['miner']] += 1
        for index, (fields, receipt) in enumerate(zip(block[1], entry['Receipts'])):
            assert receipt['status'] == '0x1' and receipt['blockHash'] == header['hash']
            assert int(receipt['blockNumber'], 16) == 15130080+number and int(receipt['transactionIndex'], 16) == index
            canonical[receipt['transactionHash']] = receipt
            transactions[receipt['transactionHash']] = fields
            if number > 68:
                if receipt['transactionHash'] == cancel_hash:
                    assert receipt == cancel['Receipt'] and fields == decode_rlp(bytes.fromhex(cancel['Raw'][2:]))
                    continue
                assert fields[3] == bytes.fromhex('ff'*20) and not fields[4]
                assert int.from_bytes(decode_rlp(fields[5])[0], 'big') == 4
                native = [json.loads(bytes.fromhex(log['data'][2:])) for log in receipt['logs'] if log['topics'] == ['0x'+'0'*63+'4']]
                assert len(native) == 1 and 'Error' not in native[0]
                owner = native[0]['TicketOwner'].lower()
                assert owner in owners
                ticket = entry['Tickets'][native[0]['TicketID']]
                assert ticket['Owner'] == owner and ticket['Height'] == 15130080+number
                if i == 0:
                    new_nonces[owner].append(int.from_bytes(fields[0], 'big'))
    assert last == result['Final']['hash']
assert source['Stale']['hash'] not in canonical
assert result['ProducedThroughLive'] == [produced[owner] for owner in owners] and all(produced.values())
for nonce, tx in originals.items():
    assert canonical[tx['hash']]['blockHash'] != old_locations[nonce]
    assert int(canonical[tx['hash']]['blockNumber'], 16) > 15130148
    check_transaction(transactions[tx['hash']], tx)
assert transactions[saved_hash] == saved_fields
assert int(canonical[originals[39]['hash']]['blockNumber'], 16) < int(canonical[originals[40]['hash']]['blockNumber'], 16)
last_height = int(canonical[originals[40]['hash']]['blockNumber'], 16)
for tx_hash in [originals[41]['hash'], originals[42]['hash'], saved_hash]:
    height = int(canonical[tx_hash]['blockNumber'], 16)
    assert height > last_height
    last_height = height
direct = []
for nonce in range(40, 44):
    rows = [json.loads(line) for line in (evidence / f'repair/delivery-{nonce}.jsonl').read_text(encoding='utf-8').splitlines()]
    expected_hash = originals[nonce]['hash'] if nonce < 43 else saved_hash
    assert all(row['Transaction'] == expected_hash for row in rows)
    assert rows[-1]['Stage'] == 'canonical-native-success'
    assert rows[-1]['Block']['hash'] == canonical[expected_hash]['blockHash']
    if rows[-1]['DirectDelivery']:
        assert nonce < 43
        direct.append(nonce)
        delivered = [row for row in rows if row['Stage'] == 'direct-delivery-result' and row['RPCError'] == '']
        assert len(delivered) == 1 and delivered[0]['Submitted'] == expected_hash
    else:
        assert all(row['Stage'] != 'before-direct-delivery' for row in rows)
stopped = read_json(evidence / 'stopped-purchases.json')
for i, (owner, initial_nonce) in enumerate(zip(owners, (40, 63))):
    assert new_nonces[owner] == list(range(initial_nonce, initial_nonce+len(new_nonces[owner])))
    assert len(result['Purchases'][i]) >= (6 if i == 0 else 3)
    for nonce, tx in enumerate(result['Purchases'][i], initial_nonce):
        assert int(tx['nonce'], 16) == nonce and tx['hash'] in canonical
        check_transaction(transactions[tx['hash']], tx)
    cold = read_json(evidence / f'cold-intents-{("producer", "verifier")[i]}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] == initial_nonce+len(new_nonces[owner])
    assert cold['Saved'] == stopped[i]['Saved'] and cold['Saved'] != prior['Cold']['Saved']
    entries = audit['AdditionalFunding'][i]
    before = read_json(evidence / 'source-results/cold-audit.json')['AdditionalFunding'][i]
    assert len(entries) == 34 and len(before) == 33
    assert entries == {**before, cancel_hash: int(cancel['Receipt']['blockNumber'], 16)}
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
print(json.dumps({'EvidenceFiles': len(lines), 'OriginalTransactionsReincludedUnchanged': 4,
                  'SavedPurchaseIncludedUnchanged': True, 'DirectDeliveryNonces': direct,
                  'ColdLedgerBlocksPerNode': count, 'OriginalPrefixArtifactsUnchanged': 272,
                  'NewPurchaseNonces': new_nonces, 'ProducedThroughLive': produced,
                  'FinalHead': result['Final']['hash']}, indent=2))


