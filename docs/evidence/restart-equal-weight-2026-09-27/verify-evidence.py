import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

default = Path(__file__).resolve().parent
evidence = next((Path(arg).resolve() for arg in sys.argv[1:] if not arg.startswith('--')), default)
workspace = default.parents[2]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


identities = read_json(evidence / 'identities.json')
assert identities['ProductionUnchanged'] and identities['ColdExit'] == 0
for phase in ('live', 'cold'):
    assert 'WARNING: DATA RACE' not in (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
    assert int((evidence / f'{phase}-exit.txt').read_text(encoding='utf-8')) == identities[f'{phase.title()}Exit']
for name in ('test-sources.sha256', 'production-sources.sha256'):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
rows = [json.loads(line) for line in (evidence / 'equal-weight.jsonl').read_text(encoding='utf-8').splitlines()]
idle = [row for row in rows if row['Phase'] == 'idle-equal-weight']
live = [row for row in rows if row['Phase'] == 'both-mining']
assert len(idle) >= 40 and live
originals = ['0x06091659c936675419b4f309db8aa243d1d0107d9c6ed1bdc866cfbed891cc5d',
             '0xdbb89fb52cd078d8390be3f5f4e30976472d5847831627a98178c790dbccf320']
for row in idle:
    for i, node in enumerate(row['Nodes']):
        assert node['Number'] == 15130106 and node['Hash'] == originals[i]
        assert int(node['TD'], 16) == 63370514724
        assert not node['Mining'] and not node['AutoBuy']
        assert node['Full'] == node['Header'] == node['Fast'] == originals[i]
        assert len(row['Peers'][i]) == 1
        remote = row['Peers'][i][0]['protocols']['efsn']
        assert remote['head'] == originals[1-i] and remote['difficulty'] == 63370514724
idle_duration = (datetime.fromisoformat(live[0]['ObservedUTC']) - datetime.fromisoformat(idle[0]['ObservedUTC'])).total_seconds()
assert idle_duration >= 45
for row in live:
    assert all(node['Mining'] and node['AutoBuy'] for node in row['Nodes'])
result = read_json(evidence / 'equal-weight-result.json')
assert result['ForcedSync'] is False and result['NewFunding'] is False
assert result['Converged'] == (identities['LiveExit'] == 0)
audit = read_json(evidence / 'cold-audit.json')
stopped = read_json(evidence / 'stopped-purchases.json')
owners = []
for i, role in enumerate(('producer', 'verifier')):
    node = result['Stopped']['Nodes'][i]
    assert not node['Mining'] and not node['AutoBuy']
    head = audit['Heads'][i]
    assert head['hash'] == node['Hash'] and head['stateRoot'] == node['Root'] and head['mixHash'] == node['Tickets']
    assert int(head['number'], 16) == node['Number']
    assert audit['AdditionalFunding'][i] == {}
    assert stopped[i] == result['Stopped']['Purchases'][i]
    cold = read_json(evidence / f'cold-intents-{role}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] and cold['Saved'] == stopped[i]['Saved']
    owners.append({'Owner': cold['Owner'], 'Nonce': cold['Nonce'],
                   'SavedNonce': int(cold['Transaction']['nonce'], 16) if cold['Transaction'] else None})
    final_number = int(head['number'], 16) - 15130080
    assert len(list((evidence / f'blocks-{role}').glob('*.json'))) == final_number
    previous = None
    for number in range(1, final_number + 1):
        block = read_json(evidence / f'blocks-{role}' / f'block-{number:02d}.json')
        assert int(block['Header']['number'], 16) == 15130080 + number
        if previous is not None:
            assert block['Header']['parentHash'] == previous
        previous = block['Header']['hash']
        for receipt in block['Receipts']:
            assert receipt['blockHash'] == previous and receipt['status'] == '0x1'
    assert previous == head['hash']
    replay = evidence / f'fresh-replay-{role}.json'
    if replay.exists():
        proof = read_json(replay)
        assert proof['Header']['hash'] == originals[i] and proof['Blocks'] == 26
        assert proof['StateReexecuted'] and proof['OppositeHeadKnown'] is False
if result['Converged']:
    assert audit['CommonHead'] and audit['Heads'][0] == audit['Heads'][1]
    assert result['FirstCommon'] > 15130106
    assert min(node['Number'] for node in result['Live']['Nodes']) >= result['FirstCommon'] + 4
    assert result['LiveElapsedSeconds'] < 150
    for left in (evidence / 'blocks-producer').iterdir():
        assert digest(left) == digest(evidence / 'blocks-verifier' / left.name), left.name
else:
    assert result['FirstCommon'] == 0 and result['LiveElapsedSeconds'] >= 150
    assert not audit['CommonHead']
    assert all(row['Nodes'][0]['Hash'] != row['Nodes'][1]['Hash']
               and row['Nodes'][0]['TD'] == row['Nodes'][1]['TD'] for row in live)
    assert all(len(peers) == 1 for row in live for peers in row['Peers'])
    assert all(peer['protocols']['efsn']['difficulty'] <= int(node['TD'], 16)
               for row in live for node, peers in zip(row['Nodes'], row['Peers']) for peer in peers)
    assert all(owner['Nonce'] == owner['SavedNonce'] for owner in owners)
    assert all(node['Number'] > 15130108 for node in result['Stopped']['Nodes'])
    assert 'Unknown parent of propagated block' in (evidence / 'live-race.txt').read_text(encoding='utf-8')
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
print(json.dumps({'EvidenceFiles': len(lines), 'IdleObservationSeconds': idle_duration,
                  'Converged': result['Converged'], 'LiveElapsedSeconds': result['LiveElapsedSeconds'],
                  'LiveSamples': len(live),
                  'DivergentEqualWeightSamples': sum(row['Nodes'][0]['Hash'] != row['Nodes'][1]['Hash']
                      and row['Nodes'][0]['TD'] == row['Nodes'][1]['TD'] for row in live),
                  'PeerAheadSamples': sum(peer['protocols']['efsn']['difficulty'] > int(node['TD'], 16)
                      for row in live for node, peers in zip(row['Nodes'], row['Peers']) for peer in peers),
                  'ColdHeads': [head['hash'] for head in audit['Heads']], 'OwnerStates': owners}, indent=2))
