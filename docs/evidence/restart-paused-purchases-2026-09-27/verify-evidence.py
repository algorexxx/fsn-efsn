import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
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


def coverage(items, start, end):
    boundaries = {start, end} | {point for item in items for point in (item['StartTime'], item['EndTime'] + 1) if start <= point <= end}
    return min(sum(int(item['Value']) for item in items if item['StartTime'] <= point <= item['EndTime']) for point in boundaries)


identities = read_json(evidence / 'identities.json')
assert identities['ProductionUnchanged'] and identities['LiveExit'] == identities['ColdExit'] == 0
for phase in ('live', 'cold'):
    log = (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in log and '--- FAIL:' not in log
    assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == 0
for name in ('test-sources.sha256', 'production-sources.sha256'):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
source = read_json(evidence / 'source-results/pause-result.json')
result = read_json(evidence / 'paused-purchase-result.json')
audit = read_json(evidence / 'cold-audit.json')
assert audit == read_json(evidence / 'source-results/cold-audit.json')
assert audit['CommonHead'] and audit['LedgerPassed'] and result['Head'] == audit['Heads'][0]
assert result['CanonicalStateUnchanged'] and result['SavedIntentsUnchanged'] and result['PositiveControlAcceptedBoth']
assert not result['NewFunding'] and not result['MiningEnabled']
assert result['RetrievedBeforeAndAfterRestart'] == 31
assert [row['Nonce'] for row in result['Records']] == list(range(8, 40))
owner = result['Owner']
inventory = read_json(evidence / 'cold-producer.json')['Accounts'][owner]
assert inventory['Nonce'] == 8 and inventory['TicketCount'] == 0
head_time = int(result['Head']['timestamp'], 16)
original_blocks = decode_rlp((evidence / 'source-results/isolated-producer.rlp').read_bytes())
head_deadlines = []
for row in result['Records']:
    nonce, tx = row['Nonce'], row['Transaction']
    raw = (evidence / 'recovered' / f'purchase-{nonce}.rlp').read_bytes()
    fields = decode_rlp(raw)
    for index, key in ((0, 'nonce'), (1, 'gasPrice'), (2, 'gas'), (4, 'value'), (6, 'v'), (7, 'r'), (8, 's')):
        assert int.from_bytes(fields[index], 'big') == int(tx[key], 16)
    assert fields[3] == bytes.fromhex(tx['to'][2:]) and fields[5] == bytes.fromhex(tx['input'][2:])
    assert int(tx['nonce'], 16) == nonce and tx['hash'] == row['Hash']
    call = decode_rlp(fields[5])
    assert int.from_bytes(call[0], 'big') == 4
    start, end = [int.from_bytes(value, 'big') for value in decode_rlp(call[1])]
    assert row['Purchase'] == {'Start': start, 'End': end} and end >= start + 30*86400
    assert row['DeadlineBoundaryChecked'] and row['LatestPoolHeadTimestamp'] == end - 29*86400
    assert row['RemainingHeadSeconds'] == row['LatestPoolHeadTimestamp'] - head_time >= 0
    assert start <= head_time + 3*3600
    observed = int(datetime.fromisoformat(row['ObservedUTC']).timestamp())
    assert row['FundingStart'] == max(start, observed)
    assert coverage(inventory['TimeLocks']['Items'], row['FundingStart'], end) == int(row['FreeCoverageWei']) == 0
    required = 5000*10**18 + int(tx['gas'], 16)*int(tx['gasPrice'], 16)
    assert int(row['LiquidRequiredWei']) == required
    assert row['LiquidWei'] == inventory['LiquidWei']
    assert int(row['AdditionalLiquidWei']) == required - int(row['LiquidWei']) > 0
    assert len(row['PoolErrors']) == 2 and row['PoolErrors'][0] == row['PoolErrors'][1]
    assert f"insufficient balance({row['LiquidWei']}), need {required}" in row['PoolErrors'][0]
    if nonce < 39:
        matches = [block for block in original_blocks if fields in block[1]]
        assert len(matches) == 1 and int.from_bytes(matches[0][0][8], 'big') == row['OriginalHeight']
        old = read_json(previous / 'audit-isolated-producer' / f"block-{row['OriginalHeight']-15130080:02d}.json")
        assert old['Header']['hash'] == row['OriginalBlock']
    else:
        assert raw == bytes.fromhex(source['Stopped']['Purchases'][0]['Saved'][2:])
        assert row['OriginalHeight'] == 0
    head_deadlines.append((row['LatestPoolHeadTimestamp'], nonce))
stopped = read_json(evidence / 'stopped-purchases.json')
for i, role in enumerate(('producer', 'verifier')):
    status = result['Stopped'][i]
    head = audit['Heads'][i]
    assert status['Hash'] == status['Header'] == status['Fast'] == status['Full'] == head['hash']
    assert status['Root'] == head['stateRoot'] and status['Tickets'] == head['mixHash']
    assert not status['Mining'] and not status['AutoBuy']
    cold = read_json(evidence / f'cold-intents-{role}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] == source['Stopped']['Purchases'][i]['Nonce']
    assert cold['Saved'] == stopped[i]['Saved'] == source['Stopped']['Purchases'][i]['Saved']
    assert len(stopped[i]['Pending'] or []) == i and not stopped[i]['Queued']
    assert digest(evidence / f'cold-{role}.json') == digest(previous / f'cold-{role}.json')
    assert digest(evidence / f'cold-intents-{role}.json') == digest(previous / f'cold-intents-{role}.json')
    files = list((evidence / f'audit-{role}').iterdir())
    assert len(files) == 92
    for path in files:
        assert digest(path) == digest(previous / f'audit-{role}' / path.name), path.name
assert result['PositiveControl'] == read_json(evidence / 'cold-intents-verifier.json')[1]['Transaction']
assert (evidence / 'live-race.txt').read_text(encoding='utf-8').count('displaced purchase RPC recovered nonce=') == 62
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
earliest, nonce = min(head_deadlines)
print(json.dumps({'EvidenceFiles': len(lines), 'OriginalsRetrievedTwice': 31, 'UnfundedAdmissionChecks': 64,
                  'PositiveControlsAccepted': 2, 'CanonicalLedgerArtifactsUnchanged': 184,
                  'EarliestPoolHeadDeadlineUTC': datetime.fromtimestamp(earliest, timezone.utc).isoformat(),
                  'DeadlineNonce': nonce, 'FirstPurchaseAdditionalLiquidWei': result['Records'][0]['AdditionalLiquidWei']}, indent=2))
