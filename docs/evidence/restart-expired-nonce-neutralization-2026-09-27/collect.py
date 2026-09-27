import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
root = Path('D:/FusionRehearsal/expired-nonce-neutralization-2026-09-27')
source = Path('D:/FusionRehearsal/equal-weight-pause-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def retain(path, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(path.read_bytes())
    assert digest(path) == digest(destination)


assert (evidence / 'cold-exit.txt').read_text(encoding='utf-8').strip() == '0'
manifest = read_json(evidence / 'source-SHA256.json')
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
audit = read_json(root / 'cold-audit.json')
for role in ('producer', 'verifier'):
    for prefix in ('cold-', 'cold-intents-'):
        retain(root / f'{prefix}{role}.json', evidence / f'{prefix}{role}.json')
    for path in sorted((root / f'audit-{role}').glob('block-*.*')):
        retain(path, evidence / f'audit-{role}' / path.name)
for name in ('neutralizations.rlp', 'neutralizations.json', 'expired-probe.json',
             'recipient-before-mining.json', 'neutralization-result.json',
             'stopped-purchases.json', 'cold-audit.json'):
    retain(root / name, evidence / name)
for path in (root / 'source-results').iterdir():
    retain(path, evidence / 'source-results' / path.name)
changes = subprocess.check_output(['git', '-c', 'core.safecrlf=false', 'diff', '1c2d63c', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes)
identities = {'Baseline': subprocess.check_output(['git', 'rev-parse', '1c2d63c'], cwd=workspace, text=True).strip(),
              'SourceFilesUnchanged': len(manifest), 'ProductionUnchanged': True,
              'LiveExit': int((evidence / 'live-exit.txt').read_text(encoding='utf-8')),
              'ColdExit': 0, 'CommonHead': audit['CommonHead']}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identities, stream, indent=2)
    stream.write('\n')
print(json.dumps(identities, indent=2))
