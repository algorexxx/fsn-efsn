import hashlib
import json
import os
from pathlib import Path
import shutil

source = Path('/mnt/fusion-replay-copy-source')
target = Path('/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-mainnet-c')
evidence = Path('/home/rehearsal/results/restart-replay-c-storage-2026-09-24')
assert os.statvfs(source).f_flag & os.ST_RDONLY, 'source must be mounted read-only'
assert shutil.disk_usage(target.parent).free > 60 * 1024**3, 'insufficient staging reserve'
assert not target.exists(), 'copy requires a new directory'
assert not evidence.exists(), 'results require a new directory'
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
    assert shutil.disk_usage(target).free > 50 * 1024**3, 'copy reserve reached'
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as reader, destination.open('xb') as writer:
        while chunk := reader.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            writer.write(chunk)
    inventory.append({'path': path.relative_to(source).as_posix(), 'bytes': size, 'sha256': digest.hexdigest()})
for item in inventory:
    destination = target / item['path']
    digest = hashlib.sha256()
    with destination.open('rb') as reader:
        while chunk := reader.read(1024 * 1024):
            digest.update(chunk)
    assert destination.stat().st_size == item['bytes'], f'size differs: {destination}'
    assert digest.hexdigest() == item['sha256'], f'checksum differs: {destination}'
assert len([path for path in target.rglob('*') if path.is_file()]) == len(inventory)
(evidence / 'copy-manifest.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
(evidence / 'copy-verified.txt').write_text(f'files={len(inventory)} bytes={sum(item["bytes"] for item in inventory)}\n', encoding='utf-8')
print((evidence / 'copy-verified.txt').read_text(encoding='utf-8'), end='')
