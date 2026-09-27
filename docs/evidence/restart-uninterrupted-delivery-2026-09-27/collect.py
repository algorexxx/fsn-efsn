import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-participant-2026-09-26-attempt-03'
root = Path('D:/FusionRehearsal/delivered-partition-2026-09-27-attempt-04')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def retain(path, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(path.read_bytes())
    assert digest(path) == digest(target)


assert (evidence / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
manifest = read_json(evidence / 'source-SHA256.json')
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
audit = read_json(root / 'cold-audit.json')
stopped_path = root / 'stopped-purchases.json'
stopped = read_json(stopped_path) if stopped_path.exists() else None
for index, role in enumerate(('producer', 'verifier')):
    for number in range(1, 11):
        for extension in ('json', 'rlp'):
            name = f'block-{number:02d}.{extension}'
            assert digest(root / f'audit-{role}' / name) == digest(source / 'blocks' / name), role + '/' + name
    for prefix in ('preflight-', 'cold-', 'cold-intents-'):
        retain(root / f'{prefix}{role}.json', evidence / f'{prefix}{role}.json')
    if stopped is not None:
        intents = read_json(root / f'cold-intents-{role}.json')
        assert intents[index]['Nonce'] == stopped[index]['Nonce'], role
        assert intents[index]['Saved'] == stopped[index]['Saved'], role
    if role == 'verifier' and audit['CommonHead']:
        continue
    for path in sorted((root / f'audit-{role}').glob('block-*.*')):
        if int(path.stem.split('-')[-1]) > 10:
            retain(path, evidence / f'blocks-{role}' / path.name)

for name in ('before-outage.json', 'before-funding.json', 'funding-plan.json',
             'repair-result.json', 'stopped-purchases.json', 'cold-audit.json',
             'repair-branch.rlp', 'observed-0.rlp', 'observed-1.rlp',
             'isolated-producer.rlp', 'isolated-verifier.rlp', 'delivery-pools.jsonl'):
    if (root / name).exists():
        retain(root / name, evidence / name)
repair = root / 'repair'
if repair.exists():
    for path in sorted(repair.iterdir()):
        if path.is_file():
            retain(path, evidence / 'repair' / path.name)
for path in sorted((root / 'reserve-checks').glob('*.json')):
    retain(path, evidence / 'reserve-checks' / path.name)

test_hashes = {}
for line in (evidence / 'test-sources.sha256').read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ', 1)
    assert digest(workspace / relative) == expected, relative
    test_hashes[relative] = expected
changes = subprocess.check_output(['git', 'diff', '924e3cf', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes), changes
live_exit = int((evidence / 'live-exit.txt').read_text(encoding='utf-8'))
if live_exit == 0:
    result = read_json(root / 'repair-result.json')
    assert stopped is not None and audit['CommonHead']
    assert result['FundingFailure'] == '' and result['Successors'] >= 2
    assert result['OriginalsIncluded'] == result['SavedNonce'] - result['CanonicalNonce']
    assert len(result['Funding']) == 2
    assert audit['AdditionalFunding'] == [result['Funding'], result['Funding']]
    assert result['Final'] == audit['Heads'][0]['hash']
identity = {
    'Baseline': subprocess.check_output(['git', 'rev-parse', '924e3cf'], cwd=workspace, text=True).strip(),
    'ProductionUnchanged': True,
    'SourceFilesUnchanged': len(manifest),
    'Original10BlocksUnchanged': True,
    'Tests': test_hashes,
    'ColdOwnerNoncesAndSavedBytesMatchStopped': stopped is not None,
    'LiveExit': live_exit,
    'ColdExit': 0,
    'CommonHead': audit['CommonHead'],
    'ColdHeads': audit['Heads'],
}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identity, stream, indent=2)
    stream.write('\n')
print(f'{len(manifest)} source files and initial ten blocks unchanged; live exit {live_exit}, cold exit 0.')
