from pathlib import Path
import hashlib
import json
import sys

workspace = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(workspace / 'tests/restart'))
import snapshot_package

package = Path('W:/FusionRestart/restore-rehearsal-2026-09-24/package')
original = workspace / 'tmp/restart-linux/backup-copy-2026-09-23/sha256sum.txt'
original_bytes = original.read_bytes()
original_hash = hashlib.sha256(original_bytes).hexdigest()
assert original_hash == 'a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6'
expected = {}
for line in original_bytes.decode('utf-8').splitlines():
    checksum, name = line.split('  ./', 1)
    assert name not in expected
    expected[name] = checksum
manifest_hash = snapshot_package.digest(package / 'manifest.json')
manifest, parts = snapshot_package.load_package(package, manifest_hash)
actual = {item['name']: item['sha256'] for part in parts for item in part['files']}
assert actual == expected, 'packaged files differ from independently retained original backup manifest'
assert manifest['files'] == 56107 and manifest['bytes'] == 117170022674
report = {'package': str(package), 'manifest_sha256': manifest_hash, 'original_manifest_sha256': original_hash,
          'matched_original_files': len(actual), 'source_bytes': manifest['bytes'], 'parts': len(parts),
          'archive_bytes': sum(part['size'] for part in parts), 'scope': 'Every packaged source-file hash equals the original independently retained backup-copy manifest. Part checksums were read back by the packer; restore will check them again.'}
snapshot_package.write_json(Path(__file__).parent / 'source-manifest-match.json', report)
with (Path(__file__).parent / 'package-manifest.json').open('xb') as writer:
    writer.write((package / 'manifest.json').read_bytes())
print(json.dumps(report, indent=2), flush=True)
