from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for line in (here / 'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(None, 1)
    assert sha(here / name) == digest, name
r = json.loads((here / 'retire.json').read_bytes())
c = json.loads((here / 'completion.json').read_bytes())
assert r['Completed'] and c['exit'] == 0 and not c.get('outer_timeout')
assert r['ScriptSHA256'] == sha(here / 'retire.ps1')
assert (here / 'stderr.txt').stat().st_size == 0
names = ['abandonment-reorg-2026-09-27', 'equal-weight-2026-09-27',
         'stale-intent-2026-09-27', 'live-abandonment-repair-2026-09-27']
assert [e['Name'] for e in r['Entries']] == names
assert r['OtherRootsBefore'] == r['OtherRootsAfter']
assert r['SourceRootsAbsent'] == [True] * 4
assert r['Bytes'] == 4737656365 and r['Files'] == 3705
source = Path('D:/FusionRehearsal')
archive = Path('W:/FusionRestart/old-fixtures-copy-2026-10-10')
assert sha(archive / 'retire.json') == sha(here / 'retire.json')
for name in names:
    assert not (source / name).exists()
    assert (archive / name).is_dir()
assert sorted(p.name for p in source.iterdir()) == sorted(r['OtherRootsBefore'])
result = dict(passed=True, retired_sources=names, archive=str(archive),
              other_root_names_unchanged=True, files=r['Files'], logical_bytes=r['Bytes'],
              d_free_after=r['DFreeAfter'], d_free_gain=r['DFreeAfter']-r['DFreeBefore'])
assert not (here / 'verification.json').exists()
(here / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))
