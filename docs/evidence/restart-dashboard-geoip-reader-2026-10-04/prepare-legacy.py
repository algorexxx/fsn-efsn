import hashlib
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
source = root / 'tmp/fsn-stats-auth/node_modules/geoip-lite/lib'
destination = root / 'tmp/dashboard-geoip-reader/patched-legacy'
destination.mkdir(exist_ok=False)
manifest = {}
for name in ['geoip.js', 'utils.js', 'fsWatcher.js']:
    before = (source / name).read_bytes()
    after = before
    if name == 'geoip.js':
        old = b'buffer.readUInt32BE(baseOffset + 4)'
        new = b'buffer.readUInt32BE(baseOffset + 4),\n\t\tbuffer.readUInt32BE(baseOffset + 8),\n\t\tbuffer.readUInt32BE(baseOffset + 12)'
        if b'\r\n' in before:
            new = new.replace(b'\n', b'\r\n')
        assert before.count(old) == 1
        after = before.replace(old, new)
    if name == 'utils.js':
        old = b'\tif (a[1] > b[1]) return 1;'
        new = old + b'\n\tif (a[2] < b[2]) return -1;\n\tif (a[2] > b[2]) return 1;\n\tif (a[3] < b[3]) return -1;\n\tif (a[3] > b[3]) return 1;'
        if b'\r\n' in before:
            new = new.replace(b'\n', b'\r\n')
        assert before.count(old) == 1
        after = before.replace(old, new)
    (destination / name).write_bytes(after)
    manifest[name] = {'original_sha256': hashlib.sha256(before).hexdigest(), 'candidate_sha256': hashlib.sha256(after).hexdigest()}
(bundle / 'legacy-patch.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
