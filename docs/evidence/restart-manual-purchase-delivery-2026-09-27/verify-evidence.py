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


for phase in ('protocol', 'regression', 'live', 'cold'):
    assert (evidence / f'{phase}-exit.txt').read_text(encoding='utf-8').strip() == '0'
    assert 'WARNING: DATA RACE' not in (evidence / f'{phase}-race.txt').read_text(encoding='utf-8')
assert (evidence / 'protocol-exit-attempt-01.txt').read_text(encoding='utf-8').strip() == '1'
assert (evidence / 'live-attempt-01/live-exit.txt').read_text(encoding='utf-8').strip() == '1'
assert (evidence / 'live-attempt-01/cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
for phase in ('live', 'cold'):
    assert 'WARNING: DATA RACE' not in (evidence / f'live-attempt-01/{phase}-race.txt').read_text(encoding='utf-8')

initial = read_json(evidence / 'delivery-initial.json')
result = read_json(evidence / 'delivery-result.json')
stopped = read_json(evidence / 'delivery-stopped-purchases.json')
for index, role in enumerate(('producer', 'verifier')):
    cold = read_json(evidence / f'cold-intents-{role}.json')[index]
    assert cold['Saved'] == stopped[index]['Saved'] and cold['Nonce'] == stopped[index]['Nonce']
    raw = initial[index]['Saved']
    retained = read_json(evidence.parent / 'restart-live-funded-partition-2026-09-27' / f'cold-intents-{role}.json')[index]['Saved']
    assert raw == retained
    assert len(result['AutomaticSuccessors'][index]) >= 2

for name in ('same-peer-resend', 'ready-reconnect'):
    records = [json.loads(line) for line in (evidence / 'protocol' / f'{name}.jsonl').read_text(encoding='utf-8').splitlines()]
    last = records[-1]
    assert len(last['Admissions']) == 3
    first, second, final = last['Admissions']
    assert first['Error'].startswith('insufficient balance') and second['Error'].startswith('insufficient balance')
    assert first['Bytes'] == second['Bytes'] == final['Bytes']
    assert final['Error'] == '' and final['Height'] == 15130121 and final['PeerKnown']
    assert last['ReceiverStatus'] == 2

for name, directory in (('protocol-sources.sha256', workspace / 'eth'), ('live-sources.sha256', workspace)):
    for line in (evidence / name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(directory / relative) == expected, relative
first_source = evidence / 'live-attempt-01/full_state_manual_delivery_linux_test.go.txt'
first_manifest = (evidence / 'live-attempt-01/live-sources.sha256').read_text(encoding='utf-8').splitlines()
assert digest(first_source) == first_manifest[0].split('  ', 1)[0]

if '--refresh' in sys.argv:
    files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
lines = (evidence / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
for line in lines:
    expected, relative = line.split('  ', 1)
    assert digest(evidence / relative) == expected, relative
    if '--index' in sys.argv:
        path = (evidence / relative).relative_to(workspace).as_posix()
        blob = subprocess.check_output(['git', 'show', ':' + path], cwd=workspace)
        assert hashlib.sha256(blob).hexdigest() == expected, path
print(f'{len(lines)} evidence files verified; protocol admissions, saved bytes and cold identities match.')
