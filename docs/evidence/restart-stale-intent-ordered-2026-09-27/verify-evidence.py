import hashlib
import json
import subprocess
import sys
from pathlib import Path

success = Path(__file__).resolve().parent
workspace = success.parents[2]
previous = success.parent / 'restart-expired-nonce-neutralization-2026-09-27'
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


def verify_manifest(evidence):
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
    return len(lines)


def verify_attempt(evidence, passed):
    identities = read_json(evidence / 'identities.json')
    assert identities['ProductionUnchanged'] and identities['SourceFilesUnchanged'] == 599
    assert identities['LiveExit'] == (0 if passed else 1) and identities['ColdExit'] == 0
    for phase in ('live', 'cold'):
        log = (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
        assert 'WARNING: DATA RACE' not in log
        assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == (1 if phase == 'live' and not passed else 0)
        if passed or phase == 'cold':
            assert '--- FAIL:' not in log
    for name in ('test-sources.sha256', 'production-sources.sha256'):
        for line in (evidence / name).read_text(encoding='utf-8').splitlines():
            expected, relative = line.split('  ', 1)
            path = workspace / relative
            if not passed and relative == 'tests/restart/full_state_stale_intent_linux_test.go':
                path = evidence / 'full_state_stale_intent_linux_test.go.txt'
            assert digest(path) == expected, relative
    fixture = read_json(evidence / 'stale-fixture.json')
    original = read_json(evidence / 'source-results/stopped-purchases.json')[0]
    assert fixture['FixtureRecordInjection'] and not fixture['HistoricalOriginalExpired']
    assert fixture['OriginalRaw'] == original['Saved']
    assert fixture['OriginalRaw'] != fixture['StaleRaw']
    for prefix in ('Original', 'Stale'):
        check_transaction(decode_rlp(bytes.fromhex(fixture[prefix+'Raw'][2:])), fixture[prefix])
        assert int(fixture[prefix]['nonce'], 16) == 39
        assert fixture[prefix]['to'] == '0xffffffffffffffffffffffffffffffffffffffff'
    envelope = decode_rlp(bytes.fromhex(fixture['Stale']['input'][2:]))
    assert int.from_bytes(envelope[0], 'big') == 4
    start, end = [int.from_bytes(value, 'big') for value in decode_rlp(envelope[1])]
    head_time = int(fixture['Head']['timestamp'], 16)
    assert start == head_time-2*86400 and end == head_time+28*86400
    errors = 0
    for phase in (('unfunded', 'funded') if passed else ('unfunded',)):
        samples = read_json(evidence / f'{phase}-stale.json')
        assert len(samples) >= 10
        for sample in samples:
            purchase, status = sample['Purchase'], sample['Node']
            assert purchase['Nonce'] == 39 and purchase['Saved'] == fixture['StaleRaw']
            assert not purchase['Pending'] and not purchase['Queued']
            assert status['Mining'] and status['AutoBuy']
            assert sample['Errors'] == ['BuyTicket end must be greater than latest block time + 1 month'] * 2
            errors += 2
    funding = read_json(evidence / 'funding-plan.json')['Transfers']
    assert [int(tx['value'], 16) for tx in funding] == [1200*10**18, 1800*10**18]
    assert [int(tx['nonce'], 16) for tx in funding] == [233429, 45 if passed else 44]
    for tx in funding:
        assert tx['to'] == owner and int(tx['gas'], 16) == 21000 and int(tx['gasPrice'], 16) == 2_000_000_000 and tx['input'] == '0x'
    ordinary = decode_rlp((evidence / 'ordinary-transactions.rlp').read_bytes())
    historical = decode_rlp((evidence / 'source-results/neutralizations.rlp').read_bytes())
    assert len(ordinary) == (34 if passed else 33) and ordinary[:31] == historical
    for fields, tx in zip(ordinary[31:33], funding):
        check_transaction(fields, tx)
    audit = read_json(evidence / 'cold-audit.json')
    assert audit['CommonHead'] and audit['LedgerPassed'] and audit['Heads'][0] == audit['Heads'][1]
    assert audit['AdditionalFunding'][0] == audit['AdditionalFunding'][1]
    assert len(audit['AdditionalFunding'][0]) == (34 if passed else 31)
    count = int(audit['Heads'][0]['number'], 16)-15130080
    canonical = {}
    for i, role in enumerate(('producer', 'verifier')):
        inventory = read_json(evidence / f'cold-{role}.json')
        assert inventory['Header'] == audit['Heads'][i]
        assert len(list((evidence / f'audit-{role}').iterdir())) == count*2
        last = None
        for number in range(1, count+1):
            for suffix in ('json', 'rlp'):
                name = f'block-{number:02d}.{suffix}'
                path = evidence / f'audit-{role}' / name
                assert digest(path) == digest(evidence / 'audit-producer' / name)
                if number <= 50:
                    assert digest(path) == digest(previous / f'audit-{role}' / name)
            block = read_json(evidence / f'audit-{role}' / f'block-{number:02d}.json')
            assert int(block['Header']['number'], 16) == 15130080+number
            if last is not None:
                assert block['Header']['parentHash'] == last
            last = block['Header']['hash']
            for receipt in block['Receipts']:
                assert receipt['status'] == '0x1' and receipt['blockHash'] == last
                canonical[receipt['transactionHash']] = receipt
        assert last == audit['Heads'][i]['hash']
    assert fixture['Stale']['hash'] not in canonical
    live_log = (evidence / 'live-race.txt').read_text(encoding='utf-8')
    if not passed:
        assert count == 50 and audit == read_json(evidence / 'source-results/cold-audit.json')
        assert 'account has another pending transaction' in live_log
        assert 'Next block doesn\'t have ticket, wait buy ticket' in live_log
        assert 'funding transfer did not reach canonical success on both nodes' in live_log
        assert all(tx['hash'] not in canonical for tx in funding)
        assert read_json(evidence / 'cold-intents-producer.json')[0]['Saved'] == fixture['StaleRaw']
        for role in ('producer', 'verifier'):
            assert read_json(evidence / f'cold-{role}.json')['Accounts'] == read_json(previous / f'cold-{role}.json')['Accounts']
    else:
        result = read_json(evidence / 'stale-recovery-result.json')
        assert result['Before'] == fixture['Head'] and result['Final'] == audit['Heads'][0]
        assert result['DonationProduced'] and result['FixtureRecordInjection'] and not result['RecoveryRecordEdits']
        assert result['FundingWei'] == str(3000*10**18) and result['Stale'] == fixture['Stale']
        donor = read_json(evidence / 'donor-before-funding.json')
        assert donor['Nonce'] == 44 and len(donor['Pending']) == 1 and not donor['Queued']
        assert int(donor['Pending'][0]['nonce'], 16) == 44
        check_transaction(decode_rlp(bytes.fromhex(donor['Saved'][2:])), donor['Pending'][0])
        assert donor['Pending'][0]['hash'] in canonical
        funded = read_json(evidence / 'funded-stale-state.json')
        assert int(funded['Accounts'][owner]['BalancesVal'][0]) == 5021976763487999978776
        assert all(ticket['Owner'] != owner for ticket in funded['Tickets'].values())
        for tx, receipt in zip(funding, funded['Receipts']):
            assert canonical[tx['hash']] == receipt and int(receipt['gasUsed'], 16) == 21000 and not receipt['logs']
            assert audit['AdditionalFunding'][0][tx['hash']] == int(receipt['blockNumber'], 16)
        cancel = read_json(evidence / 'abandonment.json')
        tx = cancel['Transaction']
        check_transaction(ordinary[33], tx)
        check_transaction(decode_rlp(bytes.fromhex(cancel['Raw'][2:])), tx)
        assert int(tx['nonce'], 16) == 39 and tx['to'] == owner and tx['value'] == '0x0' and tx['input'] == '0x'
        assert int(tx['gas'], 16) == 21000 and int(tx['gasPrice'], 16) == 2_000_000_000
        assert canonical[tx['hash']] == result['AbandonmentReceipt']
        assert not canonical[tx['hash']]['logs'] and int(canonical[tx['hash']]['gasUsed'], 16) == 21000
        assert len(result['FreshPurchases']) >= 3
        for nonce, tx in enumerate(result['FreshPurchases'], 40):
            assert int(tx['nonce'], 16) == nonce and tx['hash'] in canonical
            receipt = canonical[tx['hash']]
            assert int(receipt['blockNumber'], 16) > int(result['AbandonmentReceipt']['blockNumber'], 16)
            native = [json.loads(bytes.fromhex(log['data'][2:])) for log in receipt['logs'] if log['topics'] == ['0x'+'0'*63+'4']]
            assert len(native) == 1 and 'Error' not in native[0] and native[0]['TicketOwner'].lower() == owner
        assert live_log.count('Automatic ticket nonce consumed without a confirmed purchase') == 1
        assert all(sample['Nodes'][i]['Mining'] and sample['Nodes'][i]['AutoBuy'] for line in (evidence / 'progress.jsonl').read_text(encoding='utf-8').splitlines() for sample in [json.loads(line)] for i in (0, 1))
        stopped = read_json(evidence / 'stopped-purchases.json')
        for i, role in enumerate(('producer', 'verifier')):
            cold = read_json(evidence / f'cold-intents-{role}.json')[i]
            assert cold['Nonce'] == stopped[i]['Nonce'] and cold['Saved'] == stopped[i]['Saved']
            assert cold['Saved'] != fixture['StaleRaw']
            assert cold['Nonce'] >= (43 if i == 0 else 48)
        included = []
        produced = set()
        for number in range(51, count+1):
            block = read_json(evidence / 'audit-producer' / f'block-{number:02d}.json')
            produced.add(block['Header']['miner'])
            fields = decode_rlp((evidence / 'audit-producer' / f'block-{number:02d}.rlp').read_bytes())
            included.extend(fields[1])
        assert produced == {owner, entrant}
        for fields in ordinary[31:]:
            assert included.count(fields) == 1
    return {'Attempt': evidence.name, 'LivePassed': passed, 'ColdBlocksPerNode': count,
            'ExpiryRPCRejections': errors, 'EvidenceFiles': verify_manifest(evidence)}


results = [verify_attempt(success.parent / 'restart-stale-intent-2026-09-27', False), verify_attempt(success, True)]
print(json.dumps(results, indent=2))


