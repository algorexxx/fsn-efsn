import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/preserved-head-state'
fork = workspace / 'tmp/full-state-partition-2026-09-26'
target = Path('D:/FusionRehearsal/equal-weight-fresh-2026-09-27')
manifest_path = workspace / 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert digest(manifest_path) == 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
assert not target.exists(), 'Preserve earlier attempts.'
entries = [line.split('  ./', 1) for line in manifest_path.read_text(encoding='utf-8').splitlines()]
assert len(entries) == 230
before = shutil.disk_usage(target.parent).free
assert before > 52 * 1024**3 + sum((source / relative).stat().st_size for _, relative in entries) * 2
identities = {}
copied = 0
count = 0


def copy(path, relative, expected=None):
    global copied, count
    assert not path.is_symlink() and workspace.resolve() in path.resolve().parents
    value = digest(path)
    assert expected is None or value == expected
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as output, path.open('rb') as stream:
        shutil.copyfileobj(stream, output, 1024 * 1024)
    assert digest(destination) == value
    identities[path.relative_to(workspace).as_posix()] = value
    copied += path.stat().st_size
    count += 1


for role in ('producer', 'verifier'):
    for expected, relative in entries:
        copy(source / relative, Path(role) / relative, expected)
    proof = {'Source': str(source), 'ManifestSHA256': digest(manifest_path), 'Files': 230}
    (target / role / 'copy-verified.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
    for path in sorted((fork / f'cold-{role}').glob('block-*.*')):
        copy(path, Path(f'original-{role}') / path.name)
    copy(fork / f'cold-{role}.json', Path(f'original-{role}.json'))
copy(fork / 'cold-sync-diagnosis.json', Path('cold-sync-diagnosis.json'))
for relative, expected in identities.items():
    assert digest(workspace / relative) == expected
with (evidence / 'source-SHA256.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(identities, stream, indent=2)
    stream.write('\n')
proof = {'Source': str(source), 'Fork': str(fork), 'Target': str(target), 'CopiedFiles': count,
         'UniqueSourceFiles': len(identities), 'Bytes': copied, 'FreeBytesBefore': before,
         'FreeBytesAfter': shutil.disk_usage(target.parent).free, 'SourcesUnchanged': True,
         'RequiresReexecutionAndHistoryInstallation': True}
with (evidence / 'copy-capacity.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, indent=2)
    stream.write('\n')
print(json.dumps(proof, indent=2))
