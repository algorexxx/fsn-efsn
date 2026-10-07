import hashlib
import json
from pathlib import Path


evidence = Path(__file__).resolve().parent
source = Path('/home/rehearsal/results/restart-release-text-2026-10-04/node')
modules = Path('/home/rehearsal/go/pkg/mod')
selections = [
    (source, 'rpc/subscription.go', 110, 186),
    (source, 'crypto/crypto.go', 74, 99),
    (source, 'trie/secure_trie.go', 106, 134),
    (source, 'trie/sync_bloom.go', 160, 173),
    (source, 'trie/database.go', 870, 895),
    (source, 'node/rpcstack.go', 174, 228),
    (source, 'log/handler.go', 39, 48),
    (source, 'log/handler.go', 247, 302),
    (source, 'internal/debug/flags.go', 116, 150),
    (source, 'p2p/discv5/ticket.go', 430, 450),
    (source, 'p2p/discv5/ticket.go', 790, 808),
    (modules, 'github.com/huin/goupnp@v1.0.3/device.go', 65, 83),
    (modules, 'github.com/!victoria!metrics/fastcache@v1.6.0/file.go', 48, 69),
]
text = []
inventory = {}
for root, name, start, end in selections:
    path = root / name
    raw = path.read_bytes()
    lines = raw.decode('utf-8').splitlines()
    inventory[str(path)] = hashlib.sha256(raw).hexdigest()
    text.append('\n' + str(path) + '\n' + '\n'.join(str(i) + ': ' + lines[i - 1] for i in range(start, min(end, len(lines)) + 1)))
(evidence / 'supporting-source.txt').write_text('\n'.join(text) + '\n', encoding='utf-8')
(evidence / 'supporting-source-hashes.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
for module, label in (('github.com/huin/goupnp@v1.0.3', 'goupnp-LICENSE'), ('github.com/!victoria!metrics/fastcache@v1.6.0', 'fastcache-LICENSE')):
    (evidence / label).write_bytes((modules / module / 'LICENSE').read_bytes())
