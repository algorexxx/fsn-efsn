import json
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
attempt_name = sys.argv[1] if len(sys.argv) > 1 else 'attempt-03'
assert attempt_name in ('attempt-01', 'attempt-03', 'attempt-04')
attempt = evidence if attempt_name == 'attempt-04' else evidence / attempt_name
owner_keys = {
    '0x2b5ad5c4795c026514f8317c7a215e218dccd6cf': '0x94a6fc29a44456b36232638a7042431c9c91b910df1c52187179085fac1560e9',
    '0x6813eb9362372eef6200f3b1dbc3f819671cba69': '0x1bec7c333d3d0c3eef8c6199a402856509c3f869d25408cc1cc2208d0371db0e',
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


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


def interval_value(items, point):
    return sum(int(item['Value']) for item in items if item['StartTime'] <= point <= item['EndTime'])


def points(items, start, end):
    return {start, end} | {point for item in items for point in (item['StartTime'], item['EndTime'] + 1)
                           if start <= point <= end}


def coverage(items, start, end):
    return min(interval_value(items, point) for point in points(items, start, end))


accounts = {}
samples = {int(path.stem.split('-')[1]): read_json(path) for path in (attempt / 'reserve-checks').glob('*.json')}
if attempt_name == 'attempt-01':
    sample = read_json(attempt / 'before-outage.json')
    samples = {int(sample['Header']['number'], 16): sample}
results = []
for path in sorted((attempt / 'blocks-producer').glob('*.json')):
    block = read_json(path)
    height = int(block['Header']['number'], 16)
    for difference in block['Differences']:
        if difference['AccountKey'] in owner_keys.values():
            accounts[difference['AccountKey']] = decode_rlp(bytes.fromhex(difference['After'][2:]))
    if height not in samples:
        continue
    sample = samples[height]
    assert sample['Header'] == block['Header']
    corrected_ready = True
    owners = []
    for record in sample['Owners']:
        owner = record['Owner']
        account = accounts[owner_keys[owner]]
        asset = bytes.fromhex('ff' * 32)
        liquid = int.from_bytes(account[3][account[2].index(asset)], 'big')
        raw = [{'StartTime': int.from_bytes(item[0], 'big'), 'EndTime': int.from_bytes(item[1], 'big'),
                'Value': int.from_bytes(item[2], 'big')}
               for item in account[5][account[4].index(asset)][0]]
        assert all(left['EndTime'] < right['StartTime'] for left, right in zip(raw, raw[1:]))
        assert liquid == int(record['LiquidWei'])
        display = record['TimeLocks']['Items']
        start, end = record['WindowStart'], record['WindowEnd']
        for point in points(raw + display, start, end):
            assert interval_value(raw, point) == interval_value(display, point)
        tickets = [ticket for ticket in block['Tickets'].values() if ticket['Owner'] == owner
                   and ticket['Height'] <= height and ticket['StartTime'] <= int(block['Header']['timestamp'], 16)
                   and ticket['ExpireTime'] >= ticket['StartTime'] + 30 * 24 * 3600
                   and ticket['ExpireTime'] > start + 15 * 60]
        assert len(tickets) == record['EligibleTickets']
        returned = raw + [{'StartTime': start, 'EndTime': ticket['ExpireTime'], 'Value': ticket['Value']}
                          for ticket in tickets]
        free = coverage(raw, start, end)
        backing = coverage(returned, start, end) + liquid
        price, gas = 5000 * 10**18, int(record['GasBudgetWei'])
        funded = liquid >= price + gas or (free >= price and liquid >= gas)
        committed = len(tickets) >= 2 and liquid >= gas and backing >= 2 * price + gas
        ready = len(tickets) > 0 and not record['NonceGap'] and (funded or committed)
        corrected_ready = corrected_ready and ready
        owners.append({'Owner': owner, 'EligibleTickets': len(tickets), 'LiquidWei': str(liquid),
                       'RecordedBackingWei': record['BackingAfterNormalSelectionWei'],
                       'RawAccountBackingWei': str(backing), 'FreeCoverageWei': str(free),
                       'TwoCommittedTickets': committed, 'Ready': ready})
    assert sample['Ready'] is (attempt_name == 'attempt-04')
    results.append({'Height': height, 'Hash': block['Header']['hash'], 'RecordedReady': sample['Ready'],
                    'CorrectedReady': corrected_ready, 'Owners': owners})

assert len(results) == (11 if attempt_name == 'attempt-03' else 1)
assert all(result['CorrectedReady'] for result in results)
assert all(int(owner['RawAccountBackingWei']) - int(owner['RecordedBackingWei']) == (0 if attempt_name == 'attempt-04' else 5000 * 10**18)
           for result in results for owner in result['Owners'])
print(json.dumps({'Attempt': attempt_name, 'RawAccountAndRPCIntervalRightsAgree': True, 'Samples': results}, indent=2))
