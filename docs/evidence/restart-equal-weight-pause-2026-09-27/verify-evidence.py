import hashlib
import json
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


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
source = read_json(evidence / 'source-results/equal-weight-result.json')
expected = read_json(evidence / 'cold-sync-diagnosis.json')
assert expected['Before'] == source['Stopped']['Nodes']
assert expected['SourceResultSHA256'] == digest(evidence / 'source-results/equal-weight-result.json')
rows = [json.loads(line) for line in (evidence / 'pause.jsonl').read_text(encoding='utf-8').splitlines()]
initial = rows[0]
assert initial['Phase'] == 'connected-idle'
for i, node in enumerate(initial['Nodes']):
    original = expected['Before'][i]
    assert node['Number'] == 15130119 and node['Hash'] == original['Hash']
    assert node['Root'] == original['Root'] and node['Tickets'] == original['Tickets']
    assert int(node['TD'], 16) == 63370514750
    assert not node['Mining'] and not node['AutoBuy']
    assert node['Full'] == node['Header'] == node['Fast'] == node['Hash']
    assert len(initial['Peers'][i]) == 1
assert (evidence / 'live-race.txt').read_text(encoding='utf-8').count('opposite-head-already-stored=false') == 2
live = [row for row in rows if row['Phase'] == 'both-mining']
paused = [row for row in rows if row['Phase'] == 'donation-paused']
assert live and paused
for row in live:
    assert all(node['Mining'] and node['AutoBuy'] for node in row['Nodes'])
    assert row['Nodes'][0]['Hash'] != row['Nodes'][1]['Hash']
for row in paused:
    assert not row['Nodes'][0]['Mining'] and not row['Nodes'][0]['AutoBuy']
    assert row['Nodes'][1]['Mining'] and row['Nodes'][1]['AutoBuy']
    assert all(len(peers) == 1 for peers in row['Peers'])
result = read_json(evidence / 'pause-result.json')
assert not result['ForcedSync'] and not result['NewFunding'] and not result['ManualRepair']
assert result['PausedProducer'] == 'donation' and result['BeforePause'] == live[-1]
before = result['BeforePause']['Nodes']
assert before[0]['Number'] >= 15130121 and before[0]['Number'] == before[1]['Number']
assert before[0]['TD'] == before[1]['TD'] and before[0]['Hash'] != before[1]['Hash']
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
    assert node['Full'] == node['Header'] == node['Fast'] == node['Hash']
    assert audit['AdditionalFunding'][i] == {}
    assert stopped[i] == result['Stopped']['Purchases'][i]
    cold = read_json(evidence / f'cold-intents-{role}.json')[i]
    assert cold['Nonce'] == stopped[i]['Nonce'] and cold['Saved'] == stopped[i]['Saved']
    owners.append({'Owner': cold['Owner'], 'Nonce': cold['Nonce'],
                   'SavedNonce': int(cold['Transaction']['nonce'], 16) if cold['Transaction'] else None})
    for prefix, tip in (('audit-', head), ('audit-isolated-', {'number': hex(before[i]['Number']), 'hash': before[i]['Hash']})):
        directory = evidence / f'{prefix}{role}'
        final_number = int(tip['number'], 16) - 15130080
        assert len(list(directory.glob('*.json'))) == final_number
        previous = None
        for number in range(1, final_number + 1):
            block = read_json(directory / f'block-{number:02d}.json')
            assert int(block['Header']['number'], 16) == 15130080 + number
            if previous is not None:
                assert block['Header']['parentHash'] == previous
            previous = block['Header']['hash']
            for receipt in block['Receipts']:
                assert receipt['blockHash'] == previous and receipt['status'] == '0x1'
        assert previous == tip['hash']
if result['Converged']:
    assert audit['CommonHead'] and audit['Heads'][0] == audit['Heads'][1]
    assert result['FirstCommon'] > before[1]['Number']
    assert min(node['Number'] for node in result['Live']['Nodes']) >= result['FirstCommon'] + 4
    assert result['PauseElapsedSeconds'] < 150
    adopted = read_json(evidence / 'audit-producer' / f"block-{before[1]['Number']-15130080:02d}.json")
    assert adopted['Header']['hash'] == before[1]['Hash']
    for left in (evidence / 'audit-producer').iterdir():
        assert digest(left) == digest(evidence / 'audit-verifier' / left.name), left.name
else:
    assert result['PauseElapsedSeconds'] >= 150
if '--refresh' in sys.argv:
    files = sorted(path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS')
    (evidence / 'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.relative_to(evidence).as_posix()}\n' for path in files), encoding='utf-8', newline='\n')
lines = (evidence / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
for line in lines:
    expected_hash, relative = line.split('  ', 1)
    assert digest(evidence / relative) == expected_hash, relative
    if '--index' in sys.argv:
        data = subprocess.check_output(['git', 'show', ':' + (evidence / relative).relative_to(workspace).as_posix()], cwd=workspace)
        assert hashlib.sha256(data).hexdigest() == expected_hash, relative
assert len(lines) == len([path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS'])
print(json.dumps({'EvidenceFiles': len(lines), 'Converged': result['Converged'],
                  'PauseElapsedSeconds': result['PauseElapsedSeconds'], 'LiveSamples': len(live),
                  'PausedSamples': len(paused), 'ColdHeads': [head['hash'] for head in audit['Heads']],
                  'OwnerStates': owners}, indent=2))
