import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-partition-2026-09-26'
target = Path('D:/FusionRehearsal/equal-weight-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert not target.exists(), 'Preserve existing attempts; choose a fresh path.'
files = [path for role in ('producer', 'verifier') for path in (source / role).rglob('*') if path.is_file()]
files.append(source / 'cold-sync-diagnosis.json')
size = sum(path.stat().st_size for path in files)
before = shutil.disk_usage(target.parent).free
assert before > 50 * 1024**3 + size + 1024**3
manifest = {}
for path in files:
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    relative = path.relative_to(source)
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    with destination.open('xb') as output, path.open('rb') as input_stream:
        shutil.copyfileobj(input_stream, output, 1024 * 1024)
    assert digest(destination) == expected
    manifest[relative.as_posix()] = expected
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
with (evidence / 'source-SHA256.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(manifest, stream, indent=2)
    stream.write('\n')
proof = {'Source': str(source), 'Target': str(target), 'Files': len(files), 'Bytes': size,
         'FreeBytesBefore': before, 'FreeBytesAfter': shutil.disk_usage(target.parent).free,
         'SourceUnchanged': True, 'HistoryAlreadyPresent': True,
         'EarlierExplicitDownloaderStoredOppositeBranchAtProducer': True}
with (evidence / 'copy-capacity.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, indent=2)
    stream.write('\n')
print(json.dumps(proof, indent=2))
