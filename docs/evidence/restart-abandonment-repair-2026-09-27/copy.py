import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
target = Path('D:/FusionRehearsal/abandonment-repair-2026-09-27')
source = Path('D:/FusionRehearsal/abandonment-reorg-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert not target.exists(), 'Preserve existing attempts; choose a fresh path.'
files = [(path, path.relative_to(source)) for role in ('producer', 'verifier')
         for path in (source / role).rglob('*') if path.is_file()]
files += [(source / name, Path('source-results') / name) for name in
          ('reorg-result.json', 'cold-audit.json', 'cold-intents-producer.json', 'cold-intents-verifier.json')]
files += [(source / 'source-results' / name, Path('source-results') / name) for name in
          ('ordinary-transactions.rlp', 'stale-recovery-result.json')]
files += [(source / 'old-branch' / f'block-{number:02d}.rlp', Path('source-results/old-branch') / f'block-{number:02d}.rlp')
          for number in range(53, 61)]
size = sum(path.stat().st_size for path, _ in files)
before = shutil.disk_usage(target.parent).free
assert before > 50 * 1024**3 + size + 1024**3
manifest = {}
for path, relative in files:
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    with destination.open('xb') as output, path.open('rb') as input_stream:
        shutil.copyfileobj(input_stream, output, 1024 * 1024)
    assert digest(destination) == expected
    manifest[path.as_posix()] = expected
for path, expected in manifest.items():
    assert digest(Path(path)) == expected, path
for name, result in (
    ('source-SHA256.json', manifest),
    ('copy-capacity.json', {'Source': str(source), 'Target': str(target),
                          'Files': len(files), 'Bytes': size, 'FreeBytesBefore': before,
                          'FreeBytesAfter': shutil.disk_usage(target.parent).free,
                          'SourceUnchanged': True, 'HistoryAlreadyPresent': True, 'NewFunding': False}),
):
    with (evidence / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
print(json.dumps(result, indent=2))
