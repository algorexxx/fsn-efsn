import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-participant-2026-09-26-attempt-03'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def retain(src, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(src.read_bytes())
    assert digest(src) == digest(target), str(src)

summaries = []
for directory, suffix in ((evidence, ''), (evidence / 'attempt-02', '-attempt-02')):
    root = Path('D:/FusionRehearsal/retry-partition-2026-09-27' + suffix)
    assert (directory / 'cold-exit.txt').read_text().strip() == '0'
    manifest = json.loads((directory / 'source-SHA256.json').read_text(encoding='utf-8'))
    for relative, expected in manifest.items():
        assert digest(source / relative) == expected, 'source changed: ' + relative
    audit = json.loads((root / 'cold-audit.json').read_text(encoding='utf-8'))
    prefix = {}
    for role in ('producer', 'verifier'):
        for index in range(1, 11):
            for extension in ('json', 'rlp'):
                name = f'block-{index:02d}.{extension}'
                expected = digest(source / 'blocks' / name)
                assert digest(root / ('audit-' + role) / name) == expected, 'prefix changed: ' + role + '/' + name
                prefix[name] = expected
        for name in ('preflight-', 'cold-', 'cold-intents-'):
            retain(root / (name + role + '.json'), directory / (name + role + '.json'))
    for name in ('before-outage.json', 'cold-audit.json', 'repair-result.json', 'stopped-purchases.json'):
        if (root / name).exists(): retain(root / name, directory / name)
    for role in ('producer', 'verifier', 'isolated-producer', 'isolated-verifier'):
        artifacts = root / ('audit-' + role)
        if role == 'verifier' and audit['CommonHead']: continue
        if not artifacts.exists(): continue
        for path in sorted(artifacts.glob('block-*.*')):
            if int(path.stem.split('-')[-1]) > 10: retain(path, directory / ('blocks-' + role) / path.name)
    repair = root / 'repair'
    if repair.exists():
        for path in repair.iterdir():
            if path.is_file(): retain(path, directory / 'repair' / path.name)
    summaries.append({'Attempt': suffix or 'initial', 'LiveExit': int((directory / 'live-exit.txt').read_text()), 'ColdExit': 0,
                      'SourceFilesUnchanged': len(manifest), 'OriginalTenBlockSHA256': prefix, 'ColdAudit': audit})

directory = evidence / 'displaced'
root = Path('D:/FusionRehearsal/retry-partition-2026-09-27-displaced')
displaced_source = Path('D:/FusionRehearsal/retry-partition-2026-09-27-attempt-02')
assert (directory / 'exit.txt').read_text().strip() == '0'
manifest = json.loads((directory / 'source-SHA256.json').read_text(encoding='utf-8'))
for relative, expected in manifest.items():
    assert digest(displaced_source / relative) == expected, 'displaced source changed: ' + relative
for index in range(1, 20):
    for extension in ('json', 'rlp'):
        name = f'block-{index:02d}.{extension}'
        assert digest(root / 'audit-displaced' / name) == digest(displaced_source / 'audit-isolated-verifier' / name)
for path in sorted((root / 'audit-displaced').glob('block-*.*')):
    if int(path.stem.split('-')[-1]) > 19: retain(path, directory / 'blocks-displaced' / path.name)
for path in sorted((root / 'recovered').iterdir()):
    retain(path, directory / 'recovered' / path.name)
retain(root / 'displaced-result.json', directory / 'displaced-result.json')

changes = subprocess.check_output(['git', 'diff', 'be86612', '--name-only', '--', '*.go'], cwd=workspace, text=True).splitlines()
assert all(path.endswith('_test.go') for path in changes), changes
identity = {
    'Baseline': subprocess.check_output(['git', 'rev-parse', 'be86612'], cwd=workspace, text=True).strip(),
    'ProductionUnchanged': True,
    'FinalTestSHA256': {p: digest(workspace / p) for p in ('tests/restart/full_state_partition_linux_test.go', 'tests/restart/full_state_retry_partition_linux_test.go')},
    'InitialTestOverride': 'initial-full_state_retry_partition_linux_test.go.txt',
    'DisplacedDiagnostic': {'SourceFilesUnchanged': len(manifest), 'FirstNineteenDisplacedBlocksUnchanged': True,
                           'Exit': 0, 'TestAddedAfterLiveRuns': 'tests/restart/full_state_displaced_audit_linux_test.go',
                           'TestSHA256': digest(workspace / 'tests/restart/full_state_displaced_audit_linux_test.go')},
    'Results': summaries,
}
with (evidence / 'identities.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identity, stream, indent=2)
    stream.write('\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
print(json.dumps([{k: v for k, v in item.items() if k not in ('OriginalTenBlockSHA256', 'ColdAudit')} for item in summaries], indent=2))
print(f'{len(files)} evidence files hashed; production Go files unchanged.')
