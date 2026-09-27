import hashlib
import json
import shutil
from pathlib import Path

evidence = Path(__file__).resolve().parent
source = Path('D:/FusionRehearsal/equal-weight-fresh-2026-09-27')
target = Path('D:/FusionRehearsal/equal-weight-pause-2026-09-27')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert not target.exists(), 'Preserve existing attempts; choose a fresh path.'
files = [path for role in ('producer', 'verifier') for path in (source / role).rglob('*') if path.is_file()]
files += [source / name for name in ('equal-weight-result.json', 'cold-audit.json')]
size = sum(path.stat().st_size for path in files)
before = shutil.disk_usage(target.parent).free
assert before > 50 * 1024**3 + size + 1024**3
manifest = {}
for path in files:
    assert not path.is_symlink() and source.resolve() in path.resolve().parents
    relative = path.relative_to(source)
    destination = target / relative
    if path.parent == source:
        destination = target / 'source-results' / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = digest(path)
    with destination.open('xb') as output, path.open('rb') as input_stream:
        shutil.copyfileobj(input_stream, output, 1024 * 1024)
    assert digest(destination) == expected
    manifest[relative.as_posix()] = expected
for relative, expected in manifest.items():
    assert digest(source / relative) == expected, relative
result = json.loads((target / 'source-results/equal-weight-result.json').read_text(encoding='utf-8'))
audit = json.loads((target / 'source-results/cold-audit.json').read_text(encoding='utf-8'))
heads = result['Stopped']['Nodes']
assert not result['Converged'] and not audit['CommonHead'] and audit['LedgerPassed']
for i, head in enumerate(heads):
    assert not head['Mining'] and not head['AutoBuy']
    assert head['Number'] == 15130119 and int(head['TD'], 16) == 63370514750
    assert head['Hash'] == audit['Heads'][i]['hash']
    assert head['Root'] == audit['Heads'][i]['stateRoot']
    assert head['Tickets'] == audit['Heads'][i]['mixHash']
with (target / 'cold-sync-diagnosis.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'Before': heads, 'DerivedFrom': 'source-results/equal-weight-result.json:Stopped.Nodes',
               'SourceResultSHA256': manifest['equal-weight-result.json'],
               'Purpose': 'Preflight expected input only; no explicit downloader diagnosis is run in this attempt.'}, stream, indent=2)
    stream.write('\n')
with (evidence / 'source-SHA256.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(manifest, stream, indent=2)
    stream.write('\n')
proof = {'Source': str(source), 'Target': str(target), 'Files': len(files), 'Bytes': size,
         'FreeBytesBefore': before, 'FreeBytesAfter': shutil.disk_usage(target.parent).free,
         'SourceUnchanged': True, 'HistoryAlreadyPresent': True,
         'EarlierExplicitDownloader': False}
with (evidence / 'copy-capacity.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, indent=2)
    stream.write('\n')
print(json.dumps(proof, indent=2))
