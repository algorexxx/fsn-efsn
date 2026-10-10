from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for manifest in ('INPUT_SHA256SUMS', 'LAUNCH_SHA256SUMS'):
    for line in (here / manifest).read_text(encoding='utf-8').splitlines():
        expected, name = line.split(None, 1)
        assert digest(here / name) == expected, name
record = json.loads((here / 'copy.json').read_bytes())
completion = json.loads((here / 'completion.json').read_bytes())
names = ['abandonment-reorg-2026-09-27', 'equal-weight-2026-09-27',
         'stale-intent-2026-09-27', 'live-abandonment-repair-2026-09-27']
assert completion['exit'] == 0 and not completion.get('outer_timeout')
assert record['Completed'] and record['Mode'] == 'CopyOnly'
assert record['RemovedSources'] == []
assert record['SourceRootsStillPresent'] == [True] * 4
assert record['ScriptSHA256'] == digest(here / 'copy.ps1')
assert [entry['Name'] for entry in record['Entries']] == names
files = size = 0
for entry in record['Entries']:
    name = entry['Name']
    assert entry == json.loads((here / (name + '.manifest.json')).read_bytes())
    assert entry['Source'] == 'D:\\FusionRehearsal\\' + name
    assert entry['Archive'] == 'W:\\FusionRestart\\old-fixtures-copy-2026-10-10\\' + name
    for item in entry['Inventory'].values():
        if not item['Directory']:
            assert len(item['SHA256']) == 64
            size += item['Bytes']
            files += 1
assert files == record['Files'] == 3705
assert size == record['Bytes'] == 4737656365
assert (here / 'stderr.txt').stat().st_size == 0
result = dict(passed=True, files=files, logical_bytes=size,
              copy_record_sha256=digest(here / 'copy.json'),
              scope='Completed copy records and sealed inputs; worker verified full source/archive bytes. Retirement must recheck both copies before removal.')
output = here / 'verification.json'
assert not output.exists()
output.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))
