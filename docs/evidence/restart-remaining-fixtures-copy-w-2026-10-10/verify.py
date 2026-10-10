from pathlib import Path, PureWindowsPath
import datetime
import hashlib
import json

here = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for manifest in ('INPUT_SHA256SUMS', 'LAUNCH_SHA256SUMS'):
    for line in (here / manifest).read_text(encoding='utf-8').splitlines():
        digest, name = line.split(None, 1)
        assert sha(here / name) == digest, name
record = json.loads((here / 'copy.json').read_bytes())
completion = json.loads((here / 'completion.json').read_bytes())
proposal = json.loads((here / 'proposal.json').read_bytes())
names = [entry['Name'] for entry in proposal['Entries']]
assert len(names) == 14 and len(set(names)) == 14
assert record['Completed'] and record['Mode'] == 'CopyOnly'
assert completion['exit'] == 0 and not completion.get('outer_timeout')
assert record['ScriptSHA256'] == sha(here / 'copy.ps1')
assert record['RemovedSources'] == []
assert record['SourceRootsStillPresent'] == [True] * 14
assert record['ProtectedVhdBefore'] == record['ProtectedVhdAfter']
assert record['OtherRootsBefore'] == record['OtherRootsAfter']
assert record['LockHandles'] >= 14
assert (here / 'stderr.txt').stat().st_size == 0
assert [entry['Name'] for entry in record['Entries']] == names
archive = Path('W:/FusionRestart/remaining-fixtures-copy-2026-10-10')
assert sha(archive / 'copy.json') == sha(here / 'copy.json')
files = size = 0
for entry, expected in zip(record['Entries'], proposal['Entries']):
    name = entry['Name']
    assert entry == json.loads((here / (name + '.manifest.json')).read_bytes())
    assert PureWindowsPath(entry['Source']) == PureWindowsPath('D:/FusionRehearsal') / name
    assert PureWindowsPath(entry['Archive']) == PureWindowsPath(archive) / name
    assert entry['Evidence']['ManifestSHA256'] == expected['EvidenceManifestSHA256']
    assert Path(entry['Source']).is_dir() and Path(entry['Archive']).is_dir()
    inventory = [item for item in entry['Inventory'].values() if not item['Directory']]
    assert len(inventory) == expected['Files']
    assert sum(item['Bytes'] for item in inventory) == expected['LogicalBytes']
    for item in inventory:
        assert len(item['SHA256']) == 64
        int(item['SHA256'], 16)
        files += 1
        size += item['Bytes']
assert files == record['Files'] == 9191
assert size == record['Bytes'] == 13630973746
result = dict(passed=True, verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              files=files, logical_bytes=size, roots=len(names),
              scope='Sealed inputs, completed copy records, actual root presence and archive record. Worker verified complete bytes; retirement must independently rehash both copies.',
              script_sha256=sha(Path(__file__).resolve()),
              copy_record_sha256=sha(here / 'copy.json'))
assert not (here / 'verification.json').exists()
(here / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))
