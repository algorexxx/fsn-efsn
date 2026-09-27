import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
target = Path('D:/FusionRehearsal/abandonment-reorg-2026-09-27')
local = Path('D:/FusionRehearsal/stale-intent-ordered-2026-09-27')
remote = Path('D:/FusionRehearsal/expired-nonce-neutralization-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert not target.exists(), 'Preserve existing attempts; choose a fresh path.'
files = []
for role, source in (('producer', local), ('verifier', remote)):
    files += [(path, path.relative_to(source)) for path in (source / role).rglob('*') if path.is_file()]
files += [(local / name, Path('source-results') / name) for name in
          ('stale-recovery-result.json', 'cold-audit.json', 'stopped-purchases.json', 'ordinary-transactions.rlp', 'stale-fixture.json')]
size = sum(path.stat().st_size for path, _ in files)
before = shutil.disk_usage(target.parent).free
assert before > 50 * 1024**3 + size + 1024**3
manifest = {}
for path, relative in files:
    assert not path.is_symlink() and (local.resolve() in path.resolve().parents or remote.resolve() in path.resolve().parents)
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
    ('copy-capacity.json', {'LocalSource': str(local), 'RemoteSource': str(remote), 'Target': str(target),
                          'Files': len(files), 'Bytes': size, 'FreeBytesBefore': before,
                          'FreeBytesAfter': shutil.disk_usage(target.parent).free,
                          'SourceUnchanged': True, 'HistoryAlreadyPresent': True, 'NewFunding': False}),
):
    with (evidence / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
print(json.dumps(result, indent=2))
