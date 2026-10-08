from pathlib import Path
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
DATA = HERE / 'qualification'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    record = read(DATA / 'run.json')
    assert record['completed'] and 'failure' not in record
    assert record['uid'] == 1000
    assert record['namespace'] != record['parent_namespace']
    assert all(re.fullmatch(r'net:\[\d+\]', record[x]) for x in ['namespace', 'parent_namespace'])
    assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ') and 'DOWN' in record['links']
    assert 'ro' in record['mount']['options'].split(',')
    assert record['backup_metadata_unchanged'] and record['backup_before'] == record['backup_after']
    before, after = [gzip.decompress((DATA / ('backup-metadata.' + p + '.json.gz')).read_bytes()) for p in ['before', 'after']]
    assert before == after and hashlib.sha256(before).hexdigest() == record['backup_before']['metadata_sha256']
    rows = json.loads(before)
    assert len(rows) == record['backup_before']['files']
    assert sum(row[1] for row in rows) == record['backup_before']['logical_bytes']
    assert record['capacity_bytes']['/home/rehearsal/results'] > 30*1024**3
    assert record['capacity_bytes']['/mnt/d'] > 60*1024**3
    previous = {}
    for name, expected in record['previous_manifest_sha256'].items():
        directory = HERE.parent / name
        assert sha(directory / 'SHA256SUMS') == expected
        lines = (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        for line in lines:
            digest, relative = line.split(None, 1)
            assert sha(directory / relative) == digest, (name, relative)
        previous[name] = len(lines)
    for relative, expected in record['input_sha256'].items():
        assert sha(HERE / relative) == expected, relative
    source = Path(record['source'])
    for relative, expected in record['source_sha256'].items():
        assert sha(source / relative) == expected, relative
    jwt = HERE.parent / 'restart-release-jwt-2026-10-04'
    assert sha(jwt / 'node-inventory.json') == '247cf33fbdb99c09f5036f57da906dd91ad84eb5fc6d0a6bc9565632656c72d9'
    source_inventory = read(jwt / 'node-inventory.json')
    actual_inventory = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    assert actual_inventory == source_inventory
    for name, compiler in record['toolchains'].items():
        root = Path(compiler['root'])
        assert sha(root / 'bin/go') == compiler['go_binary_sha256']
        for relative, expected in compiler['compression_source_sha256'].items():
            assert sha(root / relative) == expected
        env = compiler['go_env']
        assert env['GOPROXY'] == env['GOSUMDB'] == env['GOENV'] == 'off'
        assert env['GOTOOLCHAIN'] == 'local' and env['GOAMD64'] == 'v1'
    assert sha(DATA / 'frozen-flate-overlay.json') == record['overlay_sha256']
    overlay = read(DATA / 'frozen-flate-overlay.json')['Replace']
    old_root = Path(record['toolchains']['old']['root']) / 'src/compress/flate'
    new_root = Path(record['toolchains']['new']['root']) / 'src/compress/flate'
    old_files = {p.name: p for p in old_root.glob('*.go') if not p.name.endswith('_test.go')}
    new_files = {p.name: p for p in new_root.glob('*.go') if not p.name.endswith('_test.go')}
    assert len(old_files) == 7 and len(new_files) == 16
    assert overlay == {str(p): str(old_files[name]) if name in old_files else '' for name, p in new_files.items()}
    work = Path('/home/rehearsal/results/restart-ticket-compression-2026-10-08')
    for name, expected in record['binary_sha256'].items():
        assert sha(work / 'bin' / name) == expected
    assert [x['name'] for x in record['commands']] == ['old-build', 'new-build', 'frozen-build', 'export', 'old-compare', 'new-compare', 'frozen-compare']
    assert all(x['exit'] == 0 for x in record['commands'])
    vectors = read(DATA / 'vectors/index.json')
    assert vectors == read(DATA / 'export.stdout.txt')
    declared = re.search(r'var heights = \[\]uint64\{([^}]+)\}', (HERE / 'probe.go').read_text(encoding='utf-8'))
    assert [x['Height'] for x in vectors] == [int(x.strip()) for x in declared[1].split(',')]
    assert len(vectors) == 24
    available = [x for x in vectors if x['Available']]
    assert available and vectors[0]['Available'] and vectors[-1]['Available']
    assert vectors[0]['Header']['hash'] == '0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a'
    assert vectors[-1]['Header']['hash'] == '0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f'
    for v in vectors:
        stem = str(v['Height'])
        if not v['Available']:
            assert not (DATA / 'vectors' / (stem + '.gz')).exists()
            assert not (DATA / 'vectors' / (stem + '.rlp')).exists()
            continue
        blob = (DATA / 'vectors' / (stem + '.gz')).read_bytes()
        payload = (DATA / 'vectors' / (stem + '.rlp')).read_bytes()
        assert len(blob) == v['CompressedBytes'] and len(payload) == v['PayloadBytes']
        assert gzip.decompress(blob) == payload
    summary = {}
    for mode in ['old', 'new', 'frozen']:
        result = read(DATA / (mode + '-compare.stdout.txt'))
        assert [x['Height'] for x in result['Vectors']] == [x['Height'] for x in available]
        for v, c in zip(available, result['Vectors']):
            stem = str(v['Height'])
            actual = (DATA / mode / (stem + '.gz')).read_bytes()
            preserved = (DATA / 'vectors' / (stem + '.gz')).read_bytes()
            assert gzip.decompress(actual) == (DATA / 'vectors' / (stem + '.rlp')).read_bytes()
            assert c['ExactBytes'] == (actual == preserved)
            assert c['CommitmentMatches'] == (c['Commitment'] == v['Header']['mixHash'])
            assert c['ExactBytes'] == c['CommitmentMatches'] == (c['CacheError'] == '')
            assert c['CacheError'] in ['', 'AddCachedTickets: hash mismatch']
            assert len(actual) == c['CompressedBytes']
        summary[mode] = {'genesis_header_matches': result['Genesis'] == vectors[0]['Header'], 'exact_matches': sum(x['ExactBytes'] for x in result['Vectors']), 'cache_accepts': sum(not x['CacheError'] for x in result['Vectors']), 'mismatch_heights': [x['Height'] for x in result['Vectors'] if not x['ExactBytes']]}
    assert read(DATA / 'old-compare.stdout.txt') == read(DATA / 'frozen-compare.stdout.txt')
    report = {'verified': True, 'prior_manifests': previous, 'prior_files': sum(previous.values()), 'source_files': len(source_inventory), 'source_inventory_sha256': sha(jwt / 'node-inventory.json'), 'recorded_source_files': len(record['source_sha256']), 'commands': len(record['commands']), 'available_heights': [v['Height'] for v in available], 'unavailable_heights': [v['Height'] for v in vectors if not v['Available']], 'unique_available_blobs': len({sha(DATA / 'vectors' / (str(v['Height']) + '.gz')) for v in available}), 'comparison': summary, 'backup_metadata': record['backup_before'], 'backup_metadata_unchanged': True}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
