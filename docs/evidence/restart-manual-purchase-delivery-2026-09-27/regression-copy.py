import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
source = workspace / 'tmp/full-state-existing-funds-2026-09-27/verifier'
target = Path('D:/FusionRehearsal/peer-purchase-retry-2026-09-27/receiver')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


assert not target.exists(), 'refusing to overwrite an existing experiment'
files = sorted(p for p in source.rglob('*') if p.is_file())
size = sum(p.stat().st_size for p in files)
assert shutil.disk_usage('D:/').free > 50 * 1024**3 + size
manifest = {}
for path in files:
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    relative = path.relative_to(source)
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    shutil.copyfile(path, destination)
    assert digest(destination) == expected
    manifest[relative.as_posix()] = expected
proof = {'Source': str(source), 'Target': str(target), 'Files': len(manifest), 'Bytes': size, 'SHA256': manifest}
encoded = json.dumps(proof, indent=2) + '\n'
(target / 'peer-retry-copy.json').write_text(encoded, encoding='utf-8', newline='\n')
(evidence / 'regression-source-copy.json').write_text(encoded, encoding='utf-8', newline='\n')
print(json.dumps({'Files': len(files), 'Bytes': size, 'FreeBytesAfterCopy': shutil.disk_usage('D:/').free}))

for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
