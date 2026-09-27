import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = Path('D:/FusionRehearsal/retry-partition-2026-09-27-attempt-02')
root = Path('D:/FusionRehearsal/funded-gap-2026-09-27')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def retain(path, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(path.read_bytes())
    assert digest(path) == digest(target)

assert (evidence / 'cold-exit.txt').read_text().strip() == '0'
manifest = json.loads((evidence / 'source-SHA256.json').read_text())
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
audit = json.loads((root / 'cold-audit.json').read_text())
stopped_path = root / 'stopped-purchases.json'
stopped = json.loads(stopped_path.read_text()) if stopped_path.exists() else None
for role in ('producer', 'verifier'):
    for index in range(1, 24):
        for extension in ('json', 'rlp'):
            name = f'block-{index:02d}.{extension}'
            assert digest(root / ('audit-' + role) / name) == digest(source / 'audit-producer' / name), role + '/' + name
    for prefix in ('preflight-', 'cold-', 'cold-intents-'):
        retain(root / (prefix + role + '.json'), evidence / (prefix + role + '.json'))
    if stopped is not None:
        index = ('producer', 'verifier').index(role)
        intents = json.loads((root / ('cold-intents-' + role + '.json')).read_text())
        assert intents[index]['Nonce'] == stopped[index]['Nonce'], role
        assert intents[index]['Saved'] == stopped[index]['Saved'], role
    if role == 'verifier' and audit['CommonHead']:
        continue
    for path in sorted((root / ('audit-' + role)).glob('block-*.*')):
        if int(path.stem.split('-')[-1]) > 23:
            retain(path, evidence / ('blocks-' + role) / path.name)
for name in ('funding-plan.json', 'live-result.json', 'stopped-purchases.json', 'cold-audit.json', 'repair-branch.rlp'):
    if (root / name).exists(): retain(root / name, evidence / name)
for path in sorted((root / 'repair').iterdir()):
    retain(path, evidence / 'repair' / path.name)
for nonce in range(7, 14):
    expected = workspace / 'docs/evidence/restart-retry-partition-2026-09-27/displaced/recovered' / f'original-{nonce}.rlp'
    assert digest(root / 'repair' / expected.name) == digest(expected), nonce
test_hashes = {}
for line in (evidence / 'test-sources.sha256').read_text().splitlines():
    expected, relative = line.split('  ', 1)
    assert digest(workspace / relative) == expected, relative
    test_hashes[relative] = expected
changes = subprocess.check_output(['git', 'diff', 'e444056', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes), changes
identity = {'Baseline': subprocess.check_output(['git', 'rev-parse', 'e444056'], cwd=workspace, text=True).strip(),
            'ProductionUnchanged': True, 'SourceFilesUnchanged': len(manifest), 'Original23BlocksUnchanged': True,
            'SevenOriginalSignedTransactionsUnchanged': True, 'Tests': test_hashes,
            'ColdOwnerNoncesAndSavedBytesMatchStopped': stopped is not None,
            'LiveExit': int((evidence / 'live-exit.txt').read_text()), 'ColdExit': 0,
            'CommonHead': audit['CommonHead'], 'ColdHeads': audit['Heads']}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identity, stream, indent=2)
    stream.write('\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
print(f'{len(manifest)} source files unchanged; original 23 blocks and all seven signed originals unchanged; {len(files)} evidence files hashed.')
