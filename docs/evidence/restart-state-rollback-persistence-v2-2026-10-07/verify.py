from pathlib import Path
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FIRST = HERE.parent / 'restart-state-rollback-persistence-2026-10-07'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def mismatch(a, b, path=''):
    if type(a) != type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        return sum((mismatch(a[k], b[k], path + '/' + k) for k in a), [])
    if isinstance(a, list):
        if len(a) != len(b):
            return [(path, a, b)]
        return sum((mismatch(x, y, path + '/' + str(i)) for i, (x, y) in enumerate(zip(a, b))), [])
    return [] if a == b else [(path, a, b)]


def observations(name):
    text = (HERE / 'qualification' / (name + '.txt')).read_text(encoding='utf-8')
    values = dict((key, json.loads(value)) for key, value in re.findall(r'F11PERSIST (\S+) (.+)', text))
    roots = dict(re.findall(r'F11ROOT (\S+) (0x[0-9a-f]{64})', text))
    assert len(re.findall(r'^--- PASS: ', text, re.M)) == 1
    assert len(re.findall(r'^    --- PASS: ', text, re.M)) == 16
    assert len(values) == len(roots) == 16 and 'FAIL' not in text
    return values, roots


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
    assert not (source / 'core/state/f11_transaction_persistence_test.go').exists()
    before = (FIRST / 'transaction_persistence_test.go').read_text(encoding='utf-8')
    after = (HERE / 'transaction_persistence_test.go').read_text(encoding='utf-8')
    assert after == before.replace('TimeLocks: []*common.TimeLock{f11PersistenceLock(), new(common.TimeLock)}', 'TimeLocks: []*common.TimeLock{f11PersistenceLock(), {Items: []*common.TimeLockItem{}}}')
    patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/transaction_persistence_test.go', tofile='b/transaction_persistence_test.go'))
    assert patch == (HERE / 'fixture-correction.patch').read_text(encoding='utf-8')
    assert (FIRST / 'inspect_state_test.go').read_bytes() == (HERE / 'inspect_state_test.go').read_bytes()
    failures = (FIRST / 'qualification/baseline.txt').read_text(encoding='utf-8')
    pairs = re.findall(r'state/receipt mismatch: got=(.+) want=(.+)', failures)
    assert len(pairs) == 12
    for actual, expected in pairs:
        assert mismatch(json.loads(actual), json.loads(expected)) == [('/AfterTransaction/TimeLocks/1/Items', [], None), ('/Reopened/TimeLocks/1/Items', [], None)]
    baseline, baseline_roots = observations('baseline')
    candidate, candidate_roots = observations('candidate')
    assert baseline.keys() == candidate.keys() == baseline_roots.keys() == candidate_roots.keys()
    differing, root_differences = [], []
    for name in baseline:
        before, after = baseline[name], candidate[name]
        active_absent = bool(re.fullmatch(r'TestF11TransactionPersistence/(at|after)/(clean|dirty)_revert_absent', name))
        if active_absent:
            differing.append(name)
            for field in ['AfterTransaction', 'Reopened']:
                if field == 'Reopened' and '/clean_' in name:
                    assert before[field] == after[field]
                    continue
                old, new = before[field], after[field]
                assert old['BalanceIDs'][:-1] == new['BalanceIDs']
                assert old['BalanceIDs'][-1] == '0x02' + '00' * 31
                assert old['Balances'][:-1] == new['Balances'] == (['11'] if '/clean_' in name else ['12'])
                assert old['Balances'][-1] == ('<nil>' if field == 'AfterTransaction' else '0')
                assert {k: v for k, v in old.items() if k not in ['BalanceIDs', 'Balances']} == {k: v for k, v in new.items() if k not in ['BalanceIDs', 'Balances']}
            assert {k: v for k, v in before.items() if k not in ['AfterTransaction', 'Reopened']} == {k: v for k, v in after.items() if k not in ['AfterTransaction', 'Reopened']}
        else:
            assert before == after, name
        if baseline_roots[name] != candidate_roots[name]:
            root_differences.append(name)
        assert (baseline_roots[name] != candidate_roots[name]) == (active_absent and '/dirty_' in name), name
    assert len(differing) == 4 and len(root_differences) == 2
    gas = read_json(HERE / 'gas-vector.json')
    assert sum(gas['tested_transaction'].values()) == 31258
    assert sum(gas['prior_transaction'].values()) == 21034
    assert 1000000 - 31258 == 968742
    assert 1000000 - 21034 - 1 - 31258 == 947707
    assert 21034 + 31258 == 52292
    result = {'previous_manifest_files': previous, 'retained_overlay_input_checks': input_checks, 'runtime_and_module_hash_checks': len(record['source_sha256']), 'top_level_passes_per_selection': 1, 'subtest_passes_per_selection': 16, 'identical_observations': 12, 'only_expected_observation_differences': differing, 'only_expected_state_root_differences': root_differences, 'fixture_correction_exact': True, 'first_attempt_failures_only_empty_list_representation': len(pairs)}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
