import hashlib
import json
import os
from pathlib import Path
import shutil

source = Path('/mnt/fusion-3300000-checkpoint')
target = Path('/home/rehearsal/replay/baseline-mainnet-3300000')
evidence = Path('/home/rehearsal/results/restart-replay-3300000-2026-10-04')
assert os.statvfs(source).f_flag & os.ST_RDONLY, 'checkpoint must be read-only'
assert shutil.disk_usage(target.parent).free > 30 * 1024**3, 'insufficient Linux staging space'
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3, 'insufficient host staging space'
assert not target.exists() and not evidence.exists(), 'requires new target and results'
target.mkdir()
evidence.mkdir()
inventory = []
for path in sorted(source.rglob('*')):
    assert not path.is_symlink(), f'unexpected source symlink: {path}'
    destination = target / path.relative_to(source)
    if path.is_dir():
        destination.mkdir()
        continue
    assert path.is_file(), f'unexpected source entry: {path}'
    assert shutil.disk_usage(target).free > 20 * 1024**3, 'Linux reserve reached'
    assert shutil.disk_usage('/mnt/d').free > 50 * 1024**3, 'host reserve reached'
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as reader, destination.open('xb') as writer:
        while chunk := reader.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            writer.write(chunk)
        writer.flush()
        os.fsync(writer.fileno())
    inventory.append({'path': path.relative_to(source).as_posix(), 'bytes': size, 'sha256': digest.hexdigest()})
for item in inventory:
    destination = target / item['path']
    digest = hashlib.sha256()
    with destination.open('rb') as reader:
        while chunk := reader.read(1024 * 1024):
            digest.update(chunk)
    assert destination.stat().st_size == item['bytes'], f'size differs: {destination}'
    assert digest.hexdigest() == item['sha256'], f'checksum differs: {destination}'
assert {path.relative_to(target).as_posix() for path in target.rglob('*') if path.is_file()} == {item['path'] for item in inventory}
(evidence / 'copy-manifest.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
(evidence / 'copy-verified.txt').write_text(f'files={len(inventory)} bytes={sum(item["bytes"] for item in inventory)}\n', encoding='utf-8')
print((evidence / 'copy-verified.txt').read_text(encoding='utf-8'), end='')
