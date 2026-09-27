import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-participant-2026-09-26-attempt-03'
root = Path('D:/FusionRehearsal/live-funded-partition-2026-09-27')


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
for role in ('producer', 'verifier'):
    for index in range(1, 11):
        for extension in ('json', 'rlp'):
            name = f'block-{index:02d}.{extension}'
            assert digest(root / ('audit-' + role) / name) == digest(source / 'blocks' / name), role + '/' + name
    for prefix in ('preflight-', 'cold-', 'cold-intents-'):
        retain(root / (prefix + role + '.json'), evidence / (prefix + role + '.json'))
    if stopped is not None:
        index = ('producer', 'verifier').index(role)
        intents = read_json(root / ('cold-intents-' + role + '.json'))
        assert intents[index]['Nonce'] == stopped[index]['Nonce'], role
        assert intents[index]['Saved'] == stopped[index]['Saved'], role
    if role == 'verifier' and audit['CommonHead']:
        continue
    for path in sorted((root / ('audit-' + role)).glob('block-*.*')):
        if int(path.stem.split('-')[-1]) > 10:
            retain(path, evidence / ('blocks-' + role) / path.name)

for name in ('before-outage.json', 'before-funding.json', 'funding-plan.json',
             'repair-result.json', 'stopped-purchases.json', 'cold-audit.json',
             'repair-branch.rlp', 'observed-0.rlp', 'observed-1.rlp',
             'isolated-producer.rlp', 'isolated-verifier.rlp'):
    if (root / name).exists():
        retain(root / name, evidence / name)
repair = root / 'repair'
if repair.exists():
    for path in sorted(repair.iterdir()):
        if path.is_file():
            retain(path, evidence / 'repair' / path.name)

test_hashes = {}
for manifest_name in ('test-sources.sha256', 'admission-sources.sha256'):
    for line in (evidence / manifest_name).read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(workspace / relative) == expected, relative
        test_hashes[relative] = expected
assert (evidence / 'admission-exit.txt').read_text(encoding='utf-8').strip() == '0'
diagnostic_manifest = read_json(evidence / 'diagnostic-source-SHA256.json')
for relative, expected in diagnostic_manifest.items():
    assert digest(root / relative) == expected, relative
diagnostic = Path('D:/FusionRehearsal/live-funded-partition-2026-09-27-admission')
for path in sorted(diagnostic.glob('historical-admission-*.json')):
    retain(path, evidence / 'admission' / path.name)
retain(diagnostic / 'diagnostic-saved-producer.json', evidence / 'admission' / 'input.json')
stalled = read_json(root / 'cold-intents-producer.json')[0]
assert stalled['Saved'] == '0x' + (root / 'repair/saved.rlp').read_bytes().hex()
changes = subprocess.check_output(['git', 'diff', 'b2e3ab5', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
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
    'Baseline': subprocess.check_output(['git', 'rev-parse', 'b2e3ab5'], cwd=workspace, text=True).strip(),
    'ProductionUnchanged': True,
    'SourceFilesUnchanged': len(manifest),
    'Original10BlocksUnchanged': True,
    'DiagnosticSourceFilesUnchanged': len(diagnostic_manifest),
    'StalledSavedBytesMatchOriginal': True,
    'AdmissionExit': 0,
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
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
print(f'{len(manifest)} source files and original 10 blocks unchanged; {len(files)} evidence files hashed; live exit {identity["LiveExit"]}.')
