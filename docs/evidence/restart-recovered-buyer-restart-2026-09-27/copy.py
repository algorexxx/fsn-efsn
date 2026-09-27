import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
source = Path('D:/FusionRehearsal/stale-intent-ordered-2026-09-27')
target = Path('D:/FusionRehearsal/recovered-buyer-restart-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert not target.exists(), 'Preserve existing attempts; choose a fresh path.'
files = [path for role in ('producer', 'verifier') for path in (source / role).rglob('*') if path.is_file()]
files += [source / name for name in ('stale-recovery-result.json', 'cold-audit.json', 'stopped-purchases.json', 'ordinary-transactions.rlp', 'stale-fixture.json')]
size = sum(path.stat().st_size for path in files)
before = shutil.disk_usage(target.parent).free
assert before > 50 * 1024**3 + size + 1024**3
manifest = {}
for path in files:
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    relative = path.relative_to(source)
    destination = target / relative if path.parent != source else target / 'source-results' / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    with destination.open('xb') as output, path.open('rb') as input_stream:
        shutil.copyfileobj(input_stream, output, 1024 * 1024)
    assert digest(destination) == expected
    manifest[relative.as_posix()] = expected
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
result = json.loads((target / 'source-results/stale-recovery-result.json').read_text(encoding='utf-8'))
audit = json.loads((target / 'source-results/cold-audit.json').read_text(encoding='utf-8'))
assert audit['CommonHead'] and audit['LedgerPassed']
assert result['Final'] == audit['Heads'][0] == audit['Heads'][1]
assert int(result['Final']['number'], 16) == 15130140
assert result['Final']['hash'] == '0x81678c972fdd0e173589b25e7f7868833b9a65407218b88ad5925ca20762a061'
with (evidence / 'source-SHA256.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(manifest, stream, indent=2)
    stream.write('\n')
proof = {'Source': str(source), 'Target': str(target), 'Files': len(files), 'Bytes': size,
         'FreeBytesBefore': before, 'FreeBytesAfter': shutil.disk_usage(target.parent).free,
         'SourceUnchanged': True, 'HistoryAlreadyPresent': True, 'NewFunding': False}
with (evidence / 'copy-capacity.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, indent=2)
    stream.write('\n')
print(json.dumps(proof, indent=2))
