from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


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


    assert not (source / 'core/state/f11_api_rule_test.go').exists()
    assert not (source / 'eth/f11_fixture_support.go').exists()
    assert not (source / 'miner/f11_fixture_support.go').exists()
    assert input_checks == {'baseline': 13, 'candidate': 22}
    assert sum(previous.values()) == 275 and len(record['source_sha256']) == 35
    cases = {}
    heights = {'disabled': 15130081, 'before': 15130080, 'at': 15130081, 'after': 15130082}
    call_cases = {f'TestF11CallRuleSelection/{mode}/{selector}/{operation}'
                  for mode in heights
                  for selector in ['number', 'hash', 'latest', 'pending']
                  for operation in ['do_call', 'public_call', 'estimate', 'trace_call']}
    call_cases.update(f'TestF11CallRuleSelection/{mode}/pending_fallback/do_call' for mode in heights)
    history_cases = {f'TestF11HistoricalRuleSelection/{mode}/{operation}'
                     for mode in heights
                     for operation in ['transaction', 'block_number', 'block_hash', 'intermediate_roots']}
    system_asset, target_asset = '0x' + 'ff'*32, '0x02' + '00'*31
    revert = '00'*31 + '01'
    for selection in ['baseline', 'candidate']:
        log = (HERE / 'qualification' / (selection + '.txt')).read_text(encoding='utf-8')
        assert len(re.findall(r'^--- PASS: ', log, re.M)) == 2
        passed = re.findall(r'^    --- PASS: (\S+)', log, re.M)
        assert len(passed) == 84 and set(passed) == call_cases | history_cases
        assert not re.search(r'^\s*--- FAIL: |WARNING: DATA RACE', log, re.M)
        observations = re.findall(r'F11API (\S+) (\{[^\n]+\})', log)
        assert len(observations) == 84
        cases[selection] = {name: json.loads(value) for name, value in observations}
        assert set(cases[selection]) == call_cases | history_cases
        for name, actual in cases[selection].items():
            parts = name.split('/')
            mode, operation = parts[1], parts[-1]
            height = heights[mode]
            active = selection == 'candidate' and mode in ['at', 'after']
            history = name in history_cases
            selector = None if history else parts[2]
            head = 15130101 if history or selector in ['number', 'hash'] else height - (selector == 'pending')
            child = {
                'Exists': True,
                'BalanceIDs': [system_asset] if active else [system_asset, target_asset],
                'Balances': ['12' if history else '11'] + ([] if active else ['<nil>']),
                'TimeLockIDs': [target_asset, system_asset],
                'TimeLocks': [{'Items': [{'StartTime': 2000000001, 'EndTime': 2000000100, 'Value': '5'}]}, {'Items': []}],
                'Nonce': 7,
                'Code': '3615600657005b730500000000000000000000000000000000000000ff',
                'Storage': '0x09' + '00'*31,
            }
            expected = {'Requested': height, 'Latest': head, 'Child': child,
                        'Gas': 31258, 'Failed': True, 'Return': revert, 'Roots': None,
                        'EVMNumbers': None, 'TraceNumbers': None}
            if history:
                expected['TraceNumbers'] = [height if operation == 'transaction' else height - 1]
                if operation == 'intermediate_roots':
                    roots = actual['Roots']
                    assert len(roots) == 2 and all(re.fullmatch('0x[0-9a-f]{64}', root) and root != '0x' + '00'*32 for root in roots)
                    expected.update(Gas=0, Failed=False, Return='', Roots=roots)
            elif operation == 'trace_call':
                expected['TraceNumbers'] = [height]
            else:
                numbers = actual['EVMNumbers']
                assert numbers and all(number == height for number in numbers)
                assert len(numbers) > 1 if operation == 'estimate' else len(numbers) == 1
                expected['EVMNumbers'] = numbers
                if operation in ['public_call', 'estimate']:
                    expected['Gas'] = 0
            assert actual == expected, (selection, name)
    different = []
    for name, before in cases['baseline'].items():
        after = cases['candidate'][name]
        if name.split('/')[1] in ['at', 'after']:
            different.append(name)
            assert before['Child']['BalanceIDs'] == after['Child']['BalanceIDs'] + [target_asset]
            assert before['Child']['Balances'] == after['Child']['Balances'] + ['<nil>']
            assert {k: v for k, v in before['Child'].items() if k not in ['BalanceIDs', 'Balances']} == {k: v for k, v in after['Child'].items() if k not in ['BalanceIDs', 'Balances']}
            assert {k: v for k, v in before.items() if k != 'Child'} == {k: v for k, v in after.items() if k != 'Child'}
        else:
            assert before == after, name
    assert len(different) == 42
    result = {
        'previous_manifest_files': previous,
        'retained_overlay_input_checks': input_checks,
        'source_and_module_hash_checks': len(record['source_sha256']),
        'top_level_passes_per_selection': 2,
        'call_subtest_passes_per_selection': len(call_cases),
        'historical_subtest_passes_per_selection': len(history_cases),
        'identical_disabled_and_pre_activation_pairs': 42,
        'active_pairs_with_only_raw_child_balance_differences': different,
        'intermediate_roots_equal_across_selections': True,
        'recorded_contexts_gas_and_return_data_equal_across_selections': True,
        'database_key_value_and_pending_snapshot_invariants': 'asserted by passing Go tests; hashes/snapshots are not emitted in the logs',
        'intermediate_roots_validation': 'two nonzero roots and cross-selection equality; no independent root oracle',
    }
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
