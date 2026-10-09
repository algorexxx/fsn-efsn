from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
HEIGHTS = [100000, 300000, 600000, 900000, 1200000, 1400000, 1600000, 1800000]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


archive = read(HERE/'archive.json')
retire = read(HERE/'retire.json')
ready = read(HERE/'retire-ready.json')
assert ready['archive_sha256'] == sha(HERE/'archive.json')
assert archive['completed'] and retire['completed']
assert archive['mode'] == 'archive' and retire['mode'] == 'retire'
assert archive['script_sha256'] == retire['script_sha256'] == sha(HERE/'archive.py')
assert archive['helper_sha256'] == retire['helper_sha256'] == sha(REPO/'tests/restart/snapshot_package.py')
assert [c['height'] for c in archive['checkpoints']] == HEIGHTS
assert [c['height'] for c in retire['checkpoints']] == HEIGHTS
assert ready['sources'] == [c['source'] for c in archive['checkpoints']]
assert archive['preserved'] == retire['preserved']
assert set(archive['preserved']) == {'2000000', '2200000'}
for mode, record in [('archive', archive), ('retire', retire)]:
    assert read(HERE/(mode+'-command.json'))['exit'] == 0
    assert not (HERE/(mode+'.stderr.txt')).read_bytes()
    assert record['mount']['source'] == 'W:' and record['mount']['target'] == '/mnt/w'
    assert record['mount']['fstype'] == '9p'
    assert record['capacity_before']['/mnt/w'] > 100*1024**3
    assert record['capacity_before']['/home/rehearsal/replay'] > 20*1024**3
    assert record['capacity_before']['/mnt/d'] > 50*1024**3
files = 0
size = 0
for item, removed in zip(archive['checkpoints'], retire['checkpoints']):
    run = read(REPO/item['evidence']/'qualification/run.json')
    assert sha(REPO/item['evidence']/'qualification/run.json') == item['evidence_sha256']
    assert item['sha256'] == run['target_before_cold_sha256']
    assert set(item['files']) == set(item['sha256'])
    assert item['source'] == removed['source'] == '/home/rehearsal/replay/candidate-ticket-encoding-'+str(item['height'])
    assert item['archive'] == removed['archive'] == '/mnt/w/FusionRestart/checkpoint-archive-2026-10-09/candidate-ticket-encoding-'+str(item['height'])
    assert read(HERE/(str(item['height'])+'-retired.json')) == removed
    files += len(item['files'])
    size += sum(f['size'] for f in item['files'].values())
for record in archive['preserved'].values():
    assert sha(REPO/record['bundle']/'qualification/run.json') == record['run_sha256']
    assert read(REPO/record['bundle']/'qualification/run.json')['target_before_cold_sha256'] == record['hashes']
assert retire['capacity_after']['/home/rehearsal/replay'] > 30*1024**3
assert retire['capacity_after']['/mnt/d'] > 60*1024**3
result = {'pass': True, 'archived_heights': HEIGHTS, 'archived_files': files, 'logical_bytes': size, 'preserved_heights': [2000000, 2200000], 'free_bytes': retire['capacity_after'], 'archive_manifest_sha256': sha(HERE/'archive.json')}
with (HERE/'verification.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
