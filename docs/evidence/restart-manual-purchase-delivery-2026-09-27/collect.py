import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = Path('D:/FusionRehearsal/live-funded-partition-2026-09-27')
root = Path('D:/FusionRehearsal/manual-purchase-live-2026-09-27-attempt-02')
protocol = Path('D:/FusionRehearsal/manual-purchase-protocol-2026-09-27-attempt-02')
regression = Path('D:/FusionRehearsal/peer-purchase-retry-2026-09-27')


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


for phase in ('protocol', 'regression', 'live', 'cold'):
    assert (evidence / f'{phase}-exit.txt').read_text(encoding='utf-8').strip() == '0', phase
for phase in ('protocol', 'live'):
    manifest = read_json(evidence / f'{phase}-source-SHA256.json')
    for relative, expected in manifest.items():
        assert digest(source / relative) == expected, relative
regression_proof = read_json(evidence / 'regression-source-copy.json')
for relative, expected in regression_proof['SHA256'].items():
    assert digest(Path(regression_proof['Source']) / relative) == expected, relative

failed_root = Path('D:/FusionRehearsal/manual-purchase-live-2026-09-27')
failed_evidence = evidence / 'live-attempt-01'
assert (failed_evidence / 'live-exit.txt').read_text(encoding='utf-8').strip() == '1'
assert (failed_evidence / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
failed_audit = read_json(failed_root / 'cold-audit.json')
assert failed_audit['CommonHead'] and failed_audit['LedgerPassed']
for role in ('producer', 'verifier'):
    for height in range(1, 46):
        for extension in ('json', 'rlp'):
            name = f'block-{height:02d}.{extension}'
            assert digest(failed_root / f'audit-{role}' / name) == digest(source / 'audit-producer' / name), name
    for prefix in ('cold-', 'cold-intents-'):
        retain(failed_root / f'{prefix}{role}.json', failed_evidence / f'{prefix}{role}.json')
for name in ('cold-audit.json', 'delivery-initial.json', 'delivery-pools.jsonl', 'direct-recipient.json'):
    retain(failed_root / name, failed_evidence / name)
for path in sorted((failed_root / 'audit-producer').glob('block-*.*')):
    if int(path.stem.split('-')[-1]) > 45:
        retain(path, failed_evidence / 'blocks' / path.name)

audit = read_json(root / 'cold-audit.json')
result = read_json(root / 'delivery-result.json')
stopped = read_json(root / 'delivery-stopped-purchases.json')
assert audit['CommonHead'] and audit['LedgerPassed']
assert result['Final'] == audit['Heads'][0] == audit['Heads'][1]
assert result['NewFunding'] is False and result['RestartedFromFailure'] is True
assert [len(items) >= 2 for items in result['AutomaticSuccessors']] == [True, True]
prior_audit = read_json(source / 'cold-audit.json')
assert audit['AdditionalFunding'] == prior_audit['AdditionalFunding']
for index, role in enumerate(('producer', 'verifier')):
    intents = read_json(root / f'cold-intents-{role}.json')
    assert intents[index]['Nonce'] == stopped[index]['Nonce']
    assert intents[index]['Saved'] == stopped[index]['Saved']
    for height in range(1, 46):
        for extension in ('json', 'rlp'):
            name = f'block-{height:02d}.{extension}'
            assert digest(root / f'audit-{role}' / name) == digest(source / 'audit-producer' / name), name
    for prefix in ('cold-', 'cold-intents-'):
        retain(root / f'{prefix}{role}.json', evidence / f'{prefix}{role}.json')

for path in sorted((root / 'audit-producer').glob('block-*.*')):
    if int(path.stem.split('-')[-1]) > 45:
        retain(path, evidence / 'blocks' / path.name)
for name in ('cold-audit.json', 'delivery-result.json', 'delivery-initial.json', 'delivery-stopped-purchases.json', 'delivery-pools.jsonl', 'direct-recipient.json'):
    retain(root / name, evidence / name)
for name in ('same-peer-resend', 'ready-reconnect'):
    retain(protocol / f'{name}.jsonl', evidence / 'protocol' / f'{name}.jsonl')
for name in ('same-peer-resend', 'ready-reconnect', 'early-reconnect', 'automatic-rebroadcast'):
    retain(regression / f'{name}.jsonl', evidence / 'regression' / f'{name}.jsonl')
first_attempt = Path('D:/FusionRehearsal/manual-purchase-protocol-2026-09-27')
retain(first_attempt / 'same-peer-resend.jsonl', evidence / 'protocol-attempt-01.jsonl')

test_hashes = {}
for phase, directory in (('protocol', workspace / 'eth'), ('live', workspace)):
    for line in (evidence / f'{phase}-sources.sha256').read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert digest(directory / relative) == expected, relative
        test_hashes[(directory / relative).relative_to(workspace).as_posix()] = expected
changes = subprocess.check_output(['git', 'diff', '3213b81', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes), changes
identity = {
    'Baseline': subprocess.check_output(['git', 'rev-parse', '3213b81'], cwd=workspace, text=True).strip(),
    'ProductionUnchanged': True,
    'FailedLiveSourceFilesUnchanged': len(read_json(evidence / 'live-source-SHA256.json')),
    'RegressionSourceFilesUnchanged': len(regression_proof['SHA256']),
    'Retained45CanonicalBlocksUnchanged': True,
    'ColdNoncesAndSavedBytesMatchStopped': True,
    'AdditionalFundingUnchanged': True,
    'Tests': test_hashes,
    'Final': result['Final'],
}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identity, stream, indent=2)
    stream.write('\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
print(f'All source files and 45 prior blocks unchanged; {len(files)} evidence files hashed.')
