import hashlib
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
root = Path('D:/FusionRehearsal/autobuy-rebroadcast-2026-09-27')
source = workspace / 'tmp/full-state-peer-reconnect-2026-09-27'

def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def retain(src, relative):
    target = evidence / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(src.read_bytes())
    assert digest(src) == digest(target), str(src)

manifest = json.loads((evidence / 'source-copies-SHA256.json').read_text(encoding='utf-8'))
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, 'source changed: ' + relative

prefix = {}
for index in range(1, 45):
    for suffix in ('json', 'rlp'):
        name = f'block-{index:02d}.{suffix}'
        actual = digest(root / 'delivery-blocks' / name)
        assert actual == digest(source / 'diagnostic-blocks' / name), 'prefix changed: ' + name
        prefix[name] = actual

for index in range(45, 53):
    for suffix in ('json', 'rlp'):
        name = f'block-{index:02d}.{suffix}'
        retain(root / 'delivery-blocks' / name, 'blocks/' + name)

assert digest(root / 'producer-delivery-final.json') == digest(root / 'verifier-delivery-final.json')
retain(root / 'producer-delivery-final.json', 'accounts-final.json')
for name in ('delivery-pools.jsonl', 'delivery-result.json', 'delivery-stopped-purchases.json', 'unready-recipient.json'):
    retain(root / name, name)
for name in ('same-peer-resend.jsonl', 'ready-reconnect.jsonl', 'early-reconnect.jsonl', 'automatic-rebroadcast.jsonl'):
    retain(root / 'peer-purchase-retry-2026-09-27' / name, name)

result = json.loads((root / 'delivery-result.json').read_text(encoding='utf-8'))
summary = {
    'SourceFilesRechecked': len(manifest),
    'SourceUnchanged': True,
    'BothColdAccountInventoriesIdentical': True,
    'OriginalPrefixSHA256': prefix,
    'FinalHeight': int(result['Final']['number'], 16),
    'FinalHash': result['Final']['hash'],
    'NewBlocks': 8,
    'NewFunding': result['NewFunding'],
    'NewRetreats': 0,
}
with (evidence / 'retention-check.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(summary, stream, indent=2)
    stream.write('\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'OriginalPrefixSHA256'}, indent=2))
