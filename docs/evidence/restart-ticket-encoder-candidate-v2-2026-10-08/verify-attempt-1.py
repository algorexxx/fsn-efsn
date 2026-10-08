from pathlib import Path
import base64
import difflib
import gzip
import hashlib
import json
import re
import struct
import sys
import zlib

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE / 'qualification'
FIRST = HERE.parent / 'restart-ticket-encoder-candidate-2026-10-08'
PRIOR = HERE.parent / 'restart-ticket-compression-2026-10-08'
WORK = Path('/home/rehearsal/results/restart-ticket-encoder-candidate-v2-2026-10-08')
SELECTED = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def inventory(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(path.rglob('*')) if p.is_file() and '.f12-probe' not in p.parts}


def check_stream(blob, payload):
    assert gzip.decompress(blob) == payload
    assert blob[:10] == bytes.fromhex('1f8b08000000000000ff')
    assert blob[-8:] == struct.pack('<II', zlib.crc32(payload), len(payload) % 2**32)


if __name__ == '__main__':
    record = read(DATA / 'run.json')
    assert record['completed'] and 'failure' not in record and record['source_inventories_unchanged']
    assert record['uid'] == 1000 and record['namespace'] != record['parent_namespace']
    assert all(re.fullmatch(r'net:\[\d+\]', record[k]) for k in ['namespace', 'parent_namespace'])
    assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ') and 'DOWN' in record['links']
    for field in ['capacity_bytes', 'remaining_bytes']:
        assert record[field]['/home/rehearsal/results'] > 30*1024**3
        assert record[field]['/mnt/d'] > 60*1024**3
    prior_count = 0
    for name, expected in record['previous_manifest_sha256'].items():
        folder = HERE.parent / name
        assert sha(folder/'SHA256SUMS') == expected
        for line in (folder/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split(None, 1)
            assert sha(folder/relative) == digest, (name, relative)
            prior_count += 1
    for relative, expected in record['input_sha256'].items():
        assert sha(HERE/relative) == expected, relative
    for relative, expected in record['prepared_sha256'].items():
        assert sha(HERE/relative) == expected, relative
    preparation = read(HERE/'preparation.json')
    assert preparation['candidate_sha256'] == record['runtime_input_sha256']
    assert preparation['patch_sha256'] == sha(HERE/'candidate.patch')
    assert preparation['candidate_sha256'] == read(FIRST/'preparation.json')['candidate_sha256']
    assert inventory(HERE/'inputs') == preparation['candidate_sha256']
    for name, pinned in preparation['upstream'].items():
        assert sha(Path(pinned['path'])) == pinned['sha256']
        assert sha(HERE/'inputs/internal/ticketgzip/internal/flate'/name) == pinned['sha256']
    assert len(preparation['upstream']) == 5
    assert sha(Path(preparation['license']['path'])) == preparation['license']['sha256']
    assert sha(HERE/'inputs/internal/ticketgzip/internal/flate/LICENSE') == preparation['license']['sha256']
    assert sha(Path(preparation['shared_definitions']['path'])) == preparation['shared_definitions']['sha256']
    assert not any((HERE/'inputs').rglob('inflate.go')) and not any((HERE/'inputs').rglob('dict_decoder.go'))
    assert [x['exit'] for x in read(FIRST/'qualification/run.json')['commands']] == [0,1]
    assert (FIRST/'qualification/node-patch-check.stderr.txt').read_text(encoding='utf-8').count('dev/null: No such file or directory') == 9
    correction = ''
    for name in ['prepare.py', 'run.py']:
        before, after = [(folder/name).read_text(encoding='utf-8') for folder in [FIRST, HERE]]
        correction += ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/'+name, tofile='b/'+name, n=0))
    assert correction == (HERE/'attempt-correction.patch').read_text(encoding='utf-8')
    for name in ['node', 'recovery']:
        file = HERE.parent/'restart-release-jwt-2026-10-04'/(name+'-inventory.json')
        assert sha(file) == record['selected_inventory_sha256'][name]
        base = read(file)
        assert inventory(SELECTED/name) == base
        assert record['candidate_inventory'][name] == dict(base, **preparation['candidate_sha256'])
        assert inventory(WORK/name) == record['candidate_inventory'][name]
    assert inventory(WORK/'baseline') == read(HERE.parent/'restart-release-jwt-2026-10-04/node-inventory.json')
    for mode, compiler in record['toolchains'].items():
        assert sha(Path(compiler['root'])/'bin/go') == compiler['go_binary_sha256']
        env = compiler['go_env']
        assert env['GOPROXY'] == env['GOSUMDB'] == 'off' and env['GOENV'] == ''
        assert env['GOTOOLCHAIN'] == 'local' and env['GOAMD64'] == 'v1'
    for name, expected in record['binary_sha256'].items():
        assert sha(WORK/'bin'/name) == expected
    assert inventory(DATA/'fixtures') == record['fixture_sha256']
    assert all(x['exit'] == 0 for x in record['commands']) and len(record['commands']) == 27
    for mode in ['old','new','candidate']:
        build = next(x for x in record['commands'] if x['name'] == mode+'-build')
        assert '-race' in build['argv']
    assert 'WARNING: DATA RACE' not in ''.join(p.read_text(encoding='utf-8') for p in DATA.glob('*.stderr.txt'))
    payload_names = read(DATA/'fixtures/payloads/index.json')
    assert len(payload_names) == 55 and len(set(payload_names)) == 55
    mode_outputs = {mode: {'payload_matches_old': 0, 'ticket_matches_preserved': 0, 'ticket_cache_accepts': 0} for mode in ['old','new','candidate']}
    for mode in mode_outputs:
        assert read(DATA/(mode+'-payloads.stdout.txt')) == payload_names
        for name in payload_names:
            payload = (DATA/'fixtures/payloads'/(name+'.bin')).read_bytes()
            compressed = (DATA/(mode+'-payloads')/(name+'.gz')).read_bytes()
            check_stream(compressed, payload)
            if compressed == (DATA/'old-payloads'/(name+'.gz')).read_bytes():
                mode_outputs[mode]['payload_matches_old'] += 1
            if name == 'empty':
                assert compressed == bytes.fromhex('1f8b08000000000000ff010000ffff0000000000000000')
    assert mode_outputs['candidate']['payload_matches_old'] == 55
    vectors = [v for v in read(PRIOR/'qualification/vectors/index.json') if v['Available']]
    assert len(vectors) == 7
    histories = {mode: read(DATA/(mode+'-tickets.stdout.txt')) for mode in mode_outputs}
    assert histories['old'] == histories['candidate']
    assert histories['candidate']['Genesis'] == vectors[0]['Header']
    for mode, result in histories.items():
        assert [x['Name'] for x in result['Vectors']] == [str(v['Height']) for v in vectors]
        for v, row in zip(vectors, result['Vectors']):
            name = str(v['Height'])
            payload = (PRIOR/'qualification/vectors'/(name+'.rlp')).read_bytes()
            original = (PRIOR/'qualification/vectors'/(name+'.gz')).read_bytes()
            actual = (DATA/(mode+'-tickets')/(name+'.gz')).read_bytes()
            assert row['CacheInitiallyEmpty'] and row['Error'] == ''
            assert base64.b64decode(row['Before'], validate=True) == base64.b64decode(row['After'], validate=True) == payload
            check_stream(actual, payload)
            matches = actual == original
            assert matches == (row['Hash'] == v['Header']['mixHash']) == (row['CacheError'] == '')
            assert row['CacheError'] in ['', 'AddCachedTickets: hash mismatch']
            mode_outputs[mode]['ticket_matches_preserved'] += matches
            mode_outputs[mode]['ticket_cache_accepts'] += row['CacheError'] == ''
    assert mode_outputs['candidate']['ticket_matches_preserved'] == 7
    expiry_inputs = read(DATA/'fixtures/expiry.json')
    assert len(expiry_inputs) == 6
    expiry_results = {mode: read(DATA/(mode+'-expiry.stdout.txt')) for mode in mode_outputs}
    assert expiry_results['old'] == expiry_results['candidate']
    for mode, rows in expiry_results.items():
        assert [x['Name'] for x in rows] == [x['Name'] for x in expiry_inputs]
        for case, row in zip(expiry_inputs, rows):
            assert row['Error'] == case['ExpectedError']
            assert row['Before'] == case['Input'] and row['After'] == case['Expected']
            actual = (DATA/(mode+'-expiry')/(case['Name']+'.gz')).read_bytes()
            if row['Error']:
                assert actual == b'' and row['Hash'] == '0x'+'00'*32
                assert row['Root'] == '0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421'
            else:
                check_stream(actual, base64.b64decode(case['Expected'], validate=True))
                if mode == 'candidate':
                    assert actual == (DATA/'old-expiry'/(case['Name']+'.gz')).read_bytes()
    genesis = vectors[0]['Header']
    for phase in ['empty', 'restart']:
        inspection = read(DATA/('cli-'+phase+'-inspect.stdout.txt'))
        assert inspection['StoredHeader'] == genesis and inspection['Stored'] == inspection['Registered'] == genesis['hash']
        assert inspection['HeadBlock'] == inspection['HeadHeader'] == genesis['hash']
        assert inspection['HeadFast'] == '0x'+'00'*32 and inspection['Config']['chainId'] == 32659
        details = record['cli_inspections'][phase]
        assert details['unchanged_after_inspection'] and not details['restore_marker']
        console = re.findall(r'F12CLI (\{.*\})', (DATA/('cli-'+phase+'.stdout.txt')).read_text(encoding='utf-8'))
        assert len(console) == 1
        cli = json.loads(console[0])
        assert {k:v for k,v in cli.items() if k!='genesis'} == {'head':0,'network':'32659','mining':False,'autoBuy':False}
        for key, value in genesis.items():
            if key == 'baseFeePerGas':
                assert value is None and key not in cli['genesis']
            elif key in ['difficulty','number','gasLimit','gasUsed','timestamp']:
                assert int(cli['genesis'][key]) == int(value,16)
            else:
                assert cli['genesis'][key] == value, key
    assert read(DATA/'cli-empty-inspect.stdout.txt') == read(DATA/'cli-restart-inspect.stdout.txt')
    report = {'verified': True, 'prior_files': prior_count, 'runtime_and_license_files': len(preparation['candidate_sha256']), 'unchanged_upstream_writer_files': len(preparation['upstream']), 'commands': len(record['commands']), 'payloads': len(payload_names), 'historical_samples': len(vectors), 'expiry_cases': len(expiry_inputs), 'comparisons': mode_outputs, 'candidate_matches_entire_old_history_observation': True, 'candidate_matches_entire_old_expiry_observation': True, 'cli_historical_genesis_initial_and_restart': True, 'source_inventories_unchanged': True, 'release_approved': False, 'historical_replay_complete': False}
    (HERE/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
