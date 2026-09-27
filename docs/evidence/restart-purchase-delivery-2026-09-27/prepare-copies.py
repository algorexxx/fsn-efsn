import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-existing-funds-2026-09-27'
target = workspace / 'tmp/full-state-purchase-delivery-2026-09-27'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


assert not target.exists(), 'refusing to reuse a previous experiment'
files = [p for role in ['producer', 'verifier'] for p in (source / role).rglob('*') if p.is_file()]
files += [source / name for name in ['funding-recovery.json', 'diagnostic-saved-producer.json', 'diagnostic-saved-verifier.json', 'blocks/block-03.json']]
size = sum(p.stat().st_size for p in files)
assert shutil.disk_usage(workspace).free > 50 * 1024**3 + size
manifest = {}
for path in sorted(files):
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    relative = path.relative_to(source)
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    shutil.copyfile(path, destination)
    assert digest(destination) == expected
    manifest[relative.as_posix()] = expected
(evidence / 'source-copy-SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
report = {'Source': str(source), 'Target': str(target), 'Files': len(manifest), 'Bytes': size, 'FreeBytesAfterCopy': shutil.disk_usage(workspace).free}
(evidence / 'copy-capacity.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(report))
