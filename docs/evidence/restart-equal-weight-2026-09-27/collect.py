import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
root = Path('D:/FusionRehearsal/equal-weight-2026-09-27')
source = workspace / 'tmp/full-state-partition-2026-09-26'


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
    for prefix in ('preflight-', 'cold-', 'cold-intents-'):
        retain(root / f'{prefix}{role}.json', evidence / f'{prefix}{role}.json')
    for path in sorted((root / f'audit-{role}').glob('block-*.*')):
        retain(path, evidence / f'blocks-{role}' / path.name)
for name in ('equal-weight.jsonl', 'equal-weight-result.json', 'stopped-purchases.json', 'cold-audit.json'):
    if (root / name).exists():
        retain(root / name, evidence / name)
changes = subprocess.check_output(['git', '-c', 'core.safecrlf=false', 'diff', '3cfdba3', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes)
identities = {'Baseline': subprocess.check_output(['git', 'rev-parse', '3cfdba3'], cwd=workspace, text=True).strip(),
              'SourceFilesUnchanged': len(manifest), 'ProductionUnchanged': True,
              'LiveExit': int((evidence / 'live-exit.txt').read_text(encoding='utf-8')),
              'ColdExit': 0, 'CommonHead': audit['CommonHead']}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identities, stream, indent=2)
    stream.write('\n')
print(json.dumps(identities, indent=2))
