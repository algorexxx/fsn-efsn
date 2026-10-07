from pathlib import Path
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'restart-state-rollback-candidate-2026-10-07'
PORTED = HERE.parent / 'restart-state-tests-2026-10-07/verified'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def observations(name):
    text = (HERE / 'qualification' / (name + '.txt')).read_text(encoding='utf-8')
    values = dict((name, json.loads(value)) for name, value in re.findall(r'F11OBS (\S+) (.+)', text))
    assert len(re.findall(r'^--- PASS: ', text, re.M)) == 3
    assert len(re.findall(r'^    --- PASS: ', text, re.M)) == 50
    assert len(values) == 50 and 'FAIL' not in text
    return values


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
    assert len(record['runs']) == 5
    input_checks = {}
    for run in record['runs']:
        assert run['exit'] == run['expected_exit']
        replacements = read_json(HERE / 'qualification' / (run['name'] + '-overlay.json'))['Replace']
        assert set(replacements) == set(run['overlay_input_sha256'])
        for logical, physical in replacements.items():
            retained = HERE.parent / physical.split('/docs/evidence/', 1)[1]
            assert sha(retained) == run['overlay_input_sha256'][logical], (run['name'], logical)
        input_checks[run['name']] = len(replacements)
    source = Path(record['source'])
    for relative, expected in record['source_sha256'].items():
        assert sha(source / relative) == expected, relative
    base = read_json(CANDIDATE / 'base-inputs.json')
    assert str(source) == base['trees']['node']['path']
    for relative, entry in base['files'].items():
        if 'node' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
    assert not (source / 'params/suicide_timelock_fix.go').exists()
    assert not (source / 'core/state/f11_evm_rollback_test.go').exists()
    patch = ''
    for filename, old, new in [('statedb_test.go', 's.Suicide(addr)', 's.Suicide(addr, false)'), ('suicide_test.go', 'statedb.Suicide(address)', 'statedb.Suicide(address, false)')]:
        before = (PORTED / filename).read_text(encoding='utf-8')
        after = (HERE / 'candidate' / filename).read_text(encoding='utf-8')
        assert after == before.replace(old, new), filename
        patch += ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/core/state/' + filename, tofile='b/core/state/' + filename))
    assert patch == (HERE / 'test-api-adaptation.patch').read_text(encoding='utf-8')
    baseline, candidate = observations('baseline-matrix'), observations('candidate-matrix')
    assert baseline.keys() == candidate.keys()
    differing = []
    for name in baseline:
        before, after = baseline[name], candidate[name]
        if before == after:
            continue
        differing.append(name)
        if name == 'TestF11RawRollback/enabled/absent':
            assert before['BalanceIDs'][:-1] == after['BalanceIDs']
            assert before['Balances'][:-1] == after['Balances'] == ['11', '13']
            assert before['Balances'][-1] == '<nil>'
            before = {k: v for k, v in before.items() if k not in ['BalanceIDs', 'Balances']}
            after = {k: v for k, v in after.items() if k not in ['BalanceIDs', 'Balances']}
        else:
            assert re.fullmatch(r'TestF11ExecutionRollback/(at|after)/(berlin|london)/revert_absent', name), name
            assert before['Balances'] == {'Available': False, 'Panicked': True, 'Value': None}
            assert after['Balances']['Available'] and not after['Balances']['Panicked']
            before = {k: v for k, v in before.items() if k != 'Balances'}
            after = {k: v for k, v in after.items() if k != 'Balances'}
        assert before == after, name
    assert len(differing) == 5
    for name in ['baseline-original', 'candidate-original-disabled', 'candidate-original-active']:
        text = (HERE / 'qualification' / (name + '.txt')).read_text(encoding='utf-8')
        failures = re.findall(r'^    --- FAIL: (\S+)', text, re.M)
        assert failures == ([] if name.endswith('-active') else ['TestSelfdestructParentRollback/reverted_asset_without_ordinary_entry'])
        assert len(re.findall(r'^    --- PASS: ', text, re.M)) == (4 if name.endswith('-active') else 3)
        assert text.count('restored time lock independently observed as unchanged') == 3
    gas = read_json(HERE / 'gas-vector.json')
    used = sum(gas[key] for key in ['parent_pushes_before_call', 'warm_call', 'child_push', 'selfdestruct_constant', 'parent_pushes_after_call', 'mstore', 'memory_expansion', 'return_or_revert'])
    assert gas['gas_used'] == used == 5139 and gas['input'] - used == gas['gas_left'] == 194861
    result = {'previous_manifest_files': previous, 'retained_overlay_input_checks': input_checks, 'runtime_and_module_hash_checks': len(record['source_sha256']), 'matrix_top_level_passes_per_selection': 3, 'matrix_subtest_passes_per_selection': 50, 'identical_observations': 45, 'only_expected_differences': differing, 'original_baseline_and_disabled': '3 passes; retained absent-entry failure', 'original_active': '4 passes', 'test_api_adaptation_exact': True}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
