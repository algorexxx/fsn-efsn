from pathlib import Path
import hashlib
import json
import sys

here = Path(__file__).resolve().parent
mode = sys.argv[1]
assert mode in ['archive', 'retire']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
for line in (here / 'INPUT_SHA256SUMS').read_text(encoding='utf-8').splitlines():
    expected, name = line.split(None, 1)
    assert sha(here / name) == expected, name
completion = read(here / (mode + '-completion.json'))
command = read(here / (mode + '-command.json'))
record = read(here / (mode + '.json'))
assert completion['exit'] == command['exit'] == 0
assert record['completed'] and record['mode'] == mode
assert record['script_sha256'] == sha(here / 'archive.py')
assert record['helper_sha256'] == sha(here.parents[2] / 'tests/restart/snapshot_package.py')
assert record['protected_metadata_unchanged'] and record['retained_root_names_unchanged']
assert [c['height'] for c in record['checkpoints']] == [2000000, 2200000]
assert record['links'].splitlines()[0].startswith('lo ') and 'DOWN' in record['links']
assert len(record['links'].splitlines()) == 1
assert record['mount']['target'] == '/mnt/w' and record['mount']['source'] == 'W:'
assert record['capacity_after']['/home/rehearsal/replay'] > 20 * 1024**3
assert record['capacity_after']['/mnt/d'] > 50 * 1024**3
assert record['capacity_after']['/mnt/w'] > 100 * 1024**3
for name in [mode + '.stderr.txt', mode + '-host.stderr.txt']:
    assert not (here / name).read_bytes(), name
archived = read(here / 'archive.json')
files = size = 0
for item in archived['checkpoints']:
    height = item['height']
    bundle = here.parent / ('restart-ticket-encoder-replay-' + str(height) + '-2026-10-09')
    sums = {line.split(None, 1)[1]: line.split(None, 1)[0]
            for line in (bundle / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()}
    assert sha(bundle / 'qualification/run.json') == sums['qualification/run.json'] == item['evidence_sha256']
    assert sha(bundle / 'verification.json') == sums['verification.json']
    assert read(bundle / 'verification.json')['pass']
    assert item['sha256'] == read(bundle / 'qualification/run.json')['target_before_cold_sha256']
    assert set(item['files']) == set(item['sha256'])
    expected_name = 'candidate-ticket-encoding-' + str(height)
    assert item['source'] == '/home/rehearsal/replay/' + expected_name
    assert item['archive'] == '/mnt/w/FusionRestart/checkpoint-archive-2026-10-10/' + expected_name
    files += len(item['files'])
    size += sum(f['size'] for f in item['files'].values())
if mode == 'retire':
    for item, original in zip(record['checkpoints'], archived['checkpoints']):
        assert item['source'] == original['source'] and item['archive'] == original['archive']
        assert item['local_removed']
    assert read(here / 'retire-ready.json')['archive_sha256'] == sha(here / 'archive.json')
result = dict(passed=True, mode=mode, heights=[2000000, 2200000], files=files,
              logical_bytes=size, protected_metadata_unchanged=True,
              capacity_after=record['capacity_after'],
              scope='Independent record/provenance verification; each worker phase verifies full cold source/archive hashes before any removal.')
output = here / (mode + '-verification.json')
assert not output.exists()
output.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result))
