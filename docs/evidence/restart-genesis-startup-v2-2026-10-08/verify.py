from pathlib import Path
import base64
import difflib
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / 'restart-genesis-startup-2026-10-08'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_namespace(record, child, parent):
    assert record['uid'] == 1000
    assert all(re.fullmatch(r'net:\[\d+\]',record[k]) for k in [child,parent])
    assert record[child] != record[parent]
    assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ') and 'DOWN' in record['links']


if __name__ == '__main__':
    record = read_json(HERE / 'qualification/run.json')
    check_namespace(record,'network_namespace','parent_network_namespace')
    previous = {}
    for name, expected in record['previous_manifest_sha256'].items():
        directory = HERE.parent / name
        assert sha(directory / 'SHA256SUMS') == expected
        lines = (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        for line in lines:
            digest, relative = line.split(None,1)
            assert sha(directory / relative) == digest,(name,relative)
        previous[name] = len(lines)
    for name, expected in record['input_sha256'].items():
        assert sha(HERE / name) == expected,name
    for relative, expected in record['source_sha256'].items():
        assert sha(Path(record['source']) / relative) == expected,relative
    for selection, hashes in record['overlay_sha256'].items():
        overlay = read_json(HERE / 'qualification' / (selection+'-overlay.json'))['Replace']
        assert set(overlay) == set(hashes)
        for logical, physical in overlay.items():
            assert sha(Path(physical)) == hashes[logical]
    roots = {'baseline':Path('/home/rehearsal/results/restart-release-jwt-2026-10-04'),
             'candidate':Path('/home/rehearsal/results/restart-state-rollback-candidate-2026-10-07-v2')}
    for selection, root in roots.items():
        assert sha(root/'bin/efsn') == record['binary_sha256'][selection]
        assert sha(Path('/home/rehearsal/results/restart-genesis-startup-v2-2026-10-08/bin')/(selection+'-probe')) == record['helper_sha256'][selection]
    before, after = (FIRST/'run.py').read_text(encoding='utf-8'), (HERE/'run.py').read_text(encoding='utf-8')
    expected = before.replace("RUN = Path('/home/rehearsal/results/restart-genesis-startup-2026-10-08')","RUN = Path('/home/rehearsal/results/restart-genesis-startup-v2-2026-10-08')")
    expected = expected.replace("    prior[API.name] = sha(API / 'SHA256SUMS')","    prior[API.name] = sha(API / 'SHA256SUMS')\n    prior['restart-genesis-startup-2026-10-08'] = sha(HERE.parent / 'restart-genesis-startup-2026-10-08/SHA256SUMS')")
    expected = expected.replace(", '--bootnodesv4=', '--bootnodesv5='","")
    assert after == expected
    assert ''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/run.py',tofile='b/run.py')) == (HERE/'fixture-correction.patch').read_text(encoding='utf-8')
    assert [x['exit'] for x in read_json(FIRST/'qualification/run.json')['commands']] == [0,0,1]
    assert 'Bootstrap URL invalid' in (FIRST/'qualification/baseline-empty.stderr.txt').read_text(encoding='utf-8')
    assert not record['unexpected_result'] and len(record['commands']) == 12
    assert all(x['exit']==0 for x in record['commands'])
    observations = {}
    for selection in ['baseline','candidate']:
        construct = read_json(HERE/'qualification'/(selection+'-construct.stdout.txt'))
        header = construct['Direct']
        assert header == construct['Repeated'] == construct['StoredHeader']
        assert construct['Initialized'] == construct['Restarted'] == construct['Stored'] == header['hash']
        assert construct['Registered'] != header['hash']
        assert construct['Config']['chainId']==32659
        for phase in ['empty','restart']:
            name = selection+'-'+phase
            matches = re.findall(r'F12CLI (\{.*\})',(HERE/'qualification'/(name+'.stdout.txt')).read_text(encoding='utf-8'))
            assert len(matches)==1
            cli = json.loads(matches[0])
            assert {k:v for k,v in cli.items() if k!='genesis'} == {'head':0,'network':'32659','mining':False,'autoBuy':False}
            inspected = read_json(HERE/'qualification'/(name+'-inspect.stdout.txt'))
            assert inspected['StoredHeader'] == header and inspected['Stored'] == header['hash']
            assert inspected['HeadBlock'] == inspected['HeadHeader'] == header['hash']
            assert inspected['HeadFast'] == '0x'+'00'*32
            assert inspected['Config'] == construct['Config']
            g = cli['genesis']
            for key,value in header.items():
                if key=='baseFeePerGas':
                    assert value is None and key not in g
                elif key in ['difficulty','number','gasLimit','gasUsed','timestamp']:
                    assert int(g[key])==int(value,16)
                else:
                    assert g[key]==value,(name,key)
            assert g['transactions']==g['uncles']==[] and g['totalDifficulty']=='1'
            invariant = record['observations'][name]
            assert invariant['database_files_before']==invariant['database_files_after'] and invariant['readonly_bytes_unchanged']
            assert not invariant['restored_marker_present']
            observations[name] = cli
    assert all(value==observations['baseline-empty'] for value in observations.values())
    compression = read_json(HERE/'compression/run.json')
    check_namespace(compression,'namespace','parent_namespace')
    assert compression['startup_run_sha256'] == sha(HERE/'qualification/run.json')
    for relative,expected in compression['input_sha256'].items():
        assert sha(HERE/relative)==expected,relative
    for relative,expected in compression['source_sha256'].items():
        assert sha(Path(record['source'])/relative)==expected,relative
    assert len(compression['commands'])==7 and all(x['exit']==0 for x in compression['commands'])
    compiler_checks = {}
    for name,compiler in compression['toolchains'].items():
        root = Path(compiler['root'])
        assert sha(root/'bin/go') == compiler['go_binary_sha256']
        for relative,expected in compiler['compression_source_sha256'].items():
            assert sha(root/relative)==expected,relative
        compiler_checks[name] = len(compiler['compression_source_sha256'])
    assert {k:v['go_env']['GOVERSION'] for k,v in compression['toolchains'].items()}=={'old':'go1.21.3','new':'go1.27.1'}
    for name,expected in compression['binary_sha256'].items():
        assert sha(Path('/home/rehearsal/results/restart-genesis-compression-2026-10-08/bin')/name)==expected,name
    exported=read_json(HERE/'compression/export.txt')
    substituted=read_json(HERE/'compression/substitute.txt')
    payload=(HERE/'compression/tickets.rlp').read_bytes()
    assert base64.b64decode(exported['Payload'],validate=True)==base64.b64decode(substituted['Payload'],validate=True)==payload
    old=(HERE/'compression/old-compress.gz').read_bytes()
    new=(HERE/'compression/new-compress.gz').read_bytes()
    assert old!=new and gzip.decompress(old)==gzip.decompress(new)==payload
    assert old==base64.b64decode(substituted['Compressed'],validate=True)
    assert new==base64.b64decode(exported['Compressed'],validate=True)
    assert exported['Header']==header
    retained=HERE.parent/'restart-2026-09-23/responses.json'
    assert sha(retained)==compression['historical_response_sha256']
    historical=next(x['result'] for x in read_json(retained) if x['id']==2)
    assert historical==read_json(HERE/'compression/historical-genesis.json')
    assert historical['hash']==construct['Registered']
    assert set(substituted['Header'])-set(historical)=={'baseFeePerGas'}
    assert substituted['Header']['baseFeePerGas'] is None
    for key,value in substituted['Header'].items():
        if key!='baseFeePerGas':
            assert value==historical[key],key
    assert {k for k,v in exported['Header'].items() if substituted['Header'][k]!=v}=={'hash','stateRoot','mixHash'}
    report={
        'previous_manifest_files':previous,
        'source_and_module_hashes':len(record['source_sha256']),
        'startup_commands_exit_zero':12,
        'cli_start_and_restart_observations':observations,
        'readonly_database_file_comparisons':4,
        'first_fixture_failure_retained':True,
        'compression_commands_exit_zero':7,
        'compression_library_source_hashes':compiler_checks,
        'identical_ticket_rlp_bytes':len(payload),
        'gzip_bytes':{'go1.21.3':len(old),'go1.27.1':len(new)},
        'compressed_bytes_differ':True,
        'historical_header_reproduced_by_old_compressed_bytes_only':True,
        'mismatched_current_header':exported['Header'],
        'historical_header':substituted['Header'],
        'historical_blocks_beyond_genesis_qualified':False,
        'runtime_fix_selected':False,
    }
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['cli_start_and_restart_observations','mismatched_current_header','historical_header']}))
