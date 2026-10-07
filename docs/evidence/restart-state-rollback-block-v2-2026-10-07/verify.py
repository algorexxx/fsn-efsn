from pathlib import Path
import base64
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / 'restart-state-rollback-block-2026-10-07'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))



def hex_bytes(value):
    return '0x' + value.hex()


def decode(data, offset=0):
    tag = data[offset]
    if tag < 128:
        return {'value':data[offset:offset+1], 'end':offset+1}
    is_list = tag >= 192
    short = 192 if is_list else 128
    long = 247 if is_list else 183
    if tag <= long:
        length, start = tag - short, offset + 1
    else:
        width = tag - long
        start = offset + 1 + width
        length = int.from_bytes(data[offset+1:start], 'big')
    end = start + length
    assert end <= len(data)
    if not is_list:
        return {'value':data[start:end], 'end':end}
    values = []
    while start < end:
        item = decode(data, start)
        values.append(item['value'])
        start = item['end']
    assert start == end
    return {'value':values, 'end':end}


if __name__ == '__main__':
    record = read_json(HERE / 'qualification/run.json')
    previous = {}
    for name, expected_manifest in record['previous_manifest_sha256'].items():
        directory = HERE.parent / name
        assert sha(directory / 'SHA256SUMS') == expected_manifest
        lines = (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        for line in lines:
            expected, relative = line.split(None, 1)
            assert sha(directory / relative) == expected, (name, relative)
        previous[name] = len(lines)
    assert record['uid'] == 1000 and not record['unexpected_result']
    for field in ['network_namespace', 'parent_network_namespace']:
        assert re.fullmatch(r'net:\[\d+\]', record[field])
    assert record['network_namespace'] != record['parent_network_namespace']
    assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ') and 'DOWN' in record['links']
    assert len(record['runs']) == 2
    input_checks = {}
    for run in record['runs']:
        assert run['exit'] == run['expected_exit'] == 0
        replacements = read_json(HERE / 'qualification' / (run['name'] + '-overlay.json'))['Replace']
        assert set(replacements) == set(run['overlay_input_sha256'])
        for logical, physical in replacements.items():
            retained = HERE.parent / physical.split('/docs/evidence/', 1)[1]
            assert sha(retained) == run['overlay_input_sha256'][logical], (run['name'], logical)
        input_checks[run['name']] = len(replacements)
    source = Path(record['source'])
    for relative, expected in record['source_sha256'].items():
        assert sha(source / relative) == expected, relative
    base = read_json(HERE.parent / 'restart-state-rollback-candidate-2026-10-07/base-inputs.json')
    assert str(source) == base['trees']['recovery']['path']
    for relative, entry in base['files'].items():
        if 'recovery' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
    assert not (source / 'params/suicide_timelock_fix.go').exists()
    assert not (source / 'core/state/f11_block_import_test.go').exists()

    before = (FIRST / 'block_import_test.go').read_text(encoding='utf-8')
    after = (HERE / 'block_import_test.go').read_text(encoding='utf-8')
    changes = [
        ('big.NewInt(1000000))', 'big.NewInt(1000000000000000))'),
        ('BaseFee: big.NewInt(0)', 'BaseFee: big.NewInt(1000000000)'),
        ('100000, big.NewInt(1),', '100000, big.NewInt(1000000000),'),
        ('"968742"', '"968742000000000"'),
        ('"947707"', '"947707999999999"'),
        ('"312500000000031258"', '"312531258000000000"'),
        ('"312500000000052292"', '"312552292000000000"'),
    ]
    expected_source = before
    for old, new in changes:
        expected_source = expected_source.replace(old, new)
    assert after == expected_source
    patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/block_import_test.go', tofile='b/block_import_test.go'))
    assert patch == (HERE / 'fixture-correction.patch').read_text(encoding='utf-8')
    failures = (FIRST / 'qualification/baseline.txt').read_text(encoding='utf-8')
    assert len(re.findall(r'^    --- FAIL: ', failures, re.M)) == 16
    assert failures.count('invalid baseFee: have 0, want 1000000000, parentBaseFee 0, parentGasUsed 0') == 16
    assert len(read_json(FIRST / 'qualification/run.json')['runs']) == 1
    cases, process_ids = {}, set()
    for selection in ['baseline', 'candidate']:
        log = (HERE / 'qualification' / (selection + '.txt')).read_bytes()
        assert len(re.findall(rb'^--- PASS: ', log, re.M)) == 1
        assert len(re.findall(rb'^    --- PASS: ', log, re.M)) == 16
        assert not re.search(rb'^\s*--- FAIL: ', log, re.M)
        paths = sorted((HERE / 'qualification' / (selection + '-artifacts')).glob('*.json'))
        assert len(paths) == 16
        cases[selection] = {}
        for path in paths:
            case = read_json(path)
            manifest = case['Manifest']
            name = manifest['Name']
            assert name.startswith('TestF11BlockImport/')
            assert path.stem == name.split('/', 1)[1].replace('/', '_')
            expected = manifest['Expected']
            assert expected['Tickets'] == 3 and expected['Difficulty'] == '5' and expected['Order'] == 0
            prior = '/dirty_' in name
            gas = 52292 if prior else 31258
            assert expected['Sender'] == str(10**15 - gas * 10**9 - (1 if prior else 0))
            assert expected['Miner'] == str(2500000000000000000 // 8 + gas * 10**9)
            assert expected['SenderNonce'] == (2 if prior else 1)
            encoded = base64.b64decode(manifest['Block'], validate=True)
            block = decode(encoded)
            assert block['end'] == len(encoded) and len(block['value']) == 3
            header, transactions, uncles = block['value']
            assert len(header) == 16 and uncles == []
            assert hex_bytes(header[0]) == manifest['ParentHash']
            mode = name.split('/')[1]
            assert int.from_bytes(header[8], 'big') == {'disabled':15130081, 'before':15130080, 'at':15130081, 'after':15130082}[mode]
            assert int.from_bytes(header[7], 'big') == 5
            assert int.from_bytes(header[9], 'big') == 1000000
            assert int.from_bytes(header[10], 'big') == gas
            assert int.from_bytes(header[11], 'big') == 1700000120
            assert int.from_bytes(header[14], 'big') == 0
            assert int.from_bytes(header[15], 'big') == 1000000000
            assert header[6] == bytes(256)
            assert len(transactions) == (2 if prior else 1)
            for index, transaction in enumerate(transactions):
                assert len(transaction) == 9
                assert int.from_bytes(transaction[0], 'big') == index
                assert int.from_bytes(transaction[1], 'big') == 1000000000
                assert int.from_bytes(transaction[2], 'big') == 100000
                first = prior and index == 0
                assert transaction[3] == bytes([2 if first else 3]) + bytes(19)
                assert int.from_bytes(transaction[4], 'big') == (1 if first else 0)
                assert transaction[5] == (bytes([1]) if first else bytes())
            assert len(case['Results']) == len(case['Commands']) == len(case['Logs']) == 2
            for index, phase in enumerate(['import', 'cold']):
                result = case['Results'][index]
                assert result['Phase'] == phase and result['Actual'] == expected and result['CacheEmpty']
                assert result['Namespace'] == record['network_namespace']
                assert result['PID'] != case['ProducerPID']
                assert result['PID'] not in process_ids
                process_ids.add(result['PID'])
                assert result['Root'] == hex_bytes(header[3]) and result['TicketRoot'] == hex_bytes(header[13])
                assert result['Selected'] in ['0x' + format(x, '02x') + '00'*31 for x in range(1,5)]
                assert case['Commands'][index][1:] == ['-test.run=^TestF11BlockReceiver$', '-test.v', '-test.timeout=45s']
                assert '--- PASS: TestF11BlockReceiver' in case['Logs'][index] and 'FAIL' not in case['Logs'][index]
                assert f"pid={result['PID']} empty-ticket-cache=true" in case['Logs'][index]
            assert {k:v for k,v in case['Results'][0].items() if k not in ['PID','Phase']} == {k:v for k,v in case['Results'][1].items() if k not in ['PID','Phase']}
            cases[selection][name] = {'evidence':case, 'header':header, 'transactions':transactions}
    different = []
    for name, before in cases['baseline'].items():
        after = cases['candidate'][name]
        affected = bool(re.fullmatch(r'TestF11BlockImport/(at|after)/dirty_revert_absent', name))
        a, b = before['evidence'], after['evidence']
        assert a['Manifest']['ParentHash'] == b['Manifest']['ParentHash']
        assert a['Manifest']['ParentTickets'] == b['Manifest']['ParentTickets']
        old, new = a['Results'][1]['Actual'], b['Results'][1]['Actual']
        if affected:
            different.append(name)
            assert old['Child']['Balances'] == ['12', '0'] and new['Child']['Balances'] == ['12']
            assert old['Child']['BalanceIDs'][:-1] == new['Child']['BalanceIDs']
            assert old['Child']['BalanceIDs'][-1] == '0x02' + '00'*31
            assert {k:v for k,v in old['Child'].items() if k not in ['Balances','BalanceIDs']} == {k:v for k,v in new['Child'].items() if k not in ['Balances','BalanceIDs']}
            assert {k:v for k,v in old.items() if k != 'Child'} == {k:v for k,v in new.items() if k != 'Child'}
            assert before['header'][3] != after['header'][3]
            assert a['Results'][1]['Head'] != b['Results'][1]['Head']
            assert before['header'][12][:-65] == after['header'][12][:-65]
            assert [v for i,v in enumerate(before['header']) if i not in [3,12]] == [v for i,v in enumerate(after['header']) if i not in [3,12]]
            assert before['transactions'] == after['transactions']
        else:
            assert old == new and a['Manifest']['Block'] == b['Manifest']['Block']
        assert a['Results'][1]['Selected'] == b['Results'][1]['Selected']
        assert before['header'][5] == after['header'][5] and before['header'][13] == after['header'][13]
    assert len(different) == 2 and len(process_ids) == 64
    result = {'previous_manifest_files': previous, 'retained_overlay_input_checks':input_checks, 'source_and_module_hash_checks':len(record['source_sha256']), 'top_level_passes_per_selection':1, 'subtest_passes_per_selection':16, 'fresh_receiver_processes':len(process_ids), 'identical_block_encodings_and_observations':14, 'only_expected_state_root_and_account_differences':different, 'receipt_and_ticket_roots_identical_all_pairs':True, 'fixture_correction_exact':True, 'first_attempt_header_rejections':16}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
