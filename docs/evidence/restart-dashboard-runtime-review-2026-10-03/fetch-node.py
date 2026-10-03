import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
version = 'v24.21.0'
runtime = root / 'tmp/dashboard-runtime-review' / version
runtime.mkdir(parents=True, exist_ok=False)
name = 'node-' + version + '-linux-x64.tar.xz'
base = 'https://nodejs.org/dist/' + version + '/'
with urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=30) as response:
    checksums = response.read()
(bundle / 'node-shasums.txt').write_bytes(checksums)
expected = next(line.split()[0] for line in checksums.decode().splitlines() if line.split()[1] == name)
archive = runtime / name
with urllib.request.urlopen(base + name, timeout=45) as response, archive.open('wb') as target:
    while chunk := response.read(1024 * 1024):
        target.write(chunk)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
assert actual == expected
with tarfile.open(archive, 'r:xz') as source:
    for suffix in ['bin/node', 'LICENSE']:
        member = source.getmember('node-' + version + '-linux-x64/' + suffix)
        assert member.isfile()
        target = runtime / ('node' if suffix == 'bin/node' else suffix)
        target.write_bytes(source.extractfile(member).read())
record = {'version': version, 'archive_url': base + name, 'checksums_url': base + 'SHASUMS256.txt', 'archive': str(archive), 'archive_sha256': actual, 'binary': str(runtime / 'node'), 'binary_sha256': hashlib.sha256((runtime / 'node').read_bytes()).hexdigest(), 'verification': 'SHA-256 matched the official HTTPS checksum file; detached signature not verified', 'system_installation': False}
(bundle / 'node-download.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record), flush=True)
