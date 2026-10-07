from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'restart-state-rollback-candidate-2026-10-07'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    previous = {}
    for name in ['restart-state-tests-2026-10-07', 'restart-state-rollback-followup-2026-10-07', CANDIDATE.name]:
        directory = HERE.parent / name
        lines = (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        for line in lines:
            expected, relative = line.split(None, 1)
            assert sha(directory / relative) == expected, (name, relative)
        previous[name] = len(lines)

    input_checks = {}
    for name in ['qualification', 'qualification-v2', 'genesis-comparison-v2']:
        record = read_json(HERE / name / 'run.json')
        assert record['uid'] == 1000
        assert re.fullmatch(r'net:\[\d+\]', record['parent_network_namespace'])
        assert re.fullmatch(r'net:\[\d+\]', record['network_namespace'])
        assert record['network_namespace'] != record['parent_network_namespace']
        assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ')
        assert 'DOWN' in record['links']
        assert record['candidate_manifest_sha256'] == sha(CANDIDATE / 'SHA256SUMS')
        overlay = read_json(HERE / name / 'overlay.json')['Replace']
        assert set(overlay) == set(record['overlay_input_sha256'])
        for logical, physical in overlay.items():
            retained = HERE.parent / physical.split('/docs/evidence/', 1)[1]
            if name == 'qualification' and retained.name == 'startup_recovery_test.go':
                retained = HERE / 'attempt-1-startup_recovery_test.go'
            assert sha(retained) == record['overlay_input_sha256'][logical], (name, logical)
        input_checks[name] = len(overlay)
        if name == 'genesis-comparison-v2':
            baseline = read_json(HERE / name / 'baseline-overlay.json')['Replace']
            assert list(baseline) == [record['source'] + '/internal/recovery/f11_genesis_probe_test.go']
            assert baseline == {key: overlay[key] for key in baseline}
            assert read_json(HERE / name / 'candidate-overlay.json')['Replace'] == overlay
            assert [(entry['label'], entry['exit']) for entry in record['results']] == [('baseline', 1), ('candidate', 1)]
        else:
            assert record['exit'] == (1 if name == 'qualification' else 0)

    log = (HERE / 'qualification-v2/tests.txt').read_text(encoding='utf-8')
    top = re.findall(r'^--- PASS: (\S+)', log, re.M)
    sub = re.findall(r'^    --- PASS: (\S+)', log, re.M)
    assert len(top) == 5 and len(sub) == 33 and 'FAIL' not in log
    genesis = []
    for label in ['baseline', 'candidate']:
        log = (HERE / 'genesis-comparison-v2' / (label + '.txt')).read_text(encoding='utf-8')
        assert '--- FAIL: TestF11DeclaredGenesisIdentity' in log
        values = re.search(r'declared=(0x[0-9a-f]+) built=(0x[0-9a-f]+) state=(0x[0-9a-f]+)', log)
        assert values is not None and values[1] != values[2]
        genesis.append(values.groups())
    assert genesis[0] == genesis[1]
    read_json(HERE / 'genesis-comparison/overlay.json')
    for name in ['baseline-overlay.json', 'candidate-overlay.json', 'run.json']:
        path = HERE / 'genesis-comparison' / name
        assert path.read_bytes().endswith(b'\\n'), path
    for label in ['baseline', 'candidate']:
        log = (HERE / 'genesis-comparison' / (label + '.txt')).read_text(encoding='utf-8')
        assert 'parsing overlay JSON' in log and '=== RUN' not in log

    for name, vector in read_json(HERE / 'config-vectors.json').items():
        config = {'chainId': 32659, 'eip150Hash': '0x' + '0' * 64, 'datong': {'period': 15}}
        if name != 'legacy':
            config['suicideTimeLockFixBlock'] = {'effective': 100, 'different': 101}[name]
        assert vector['json'] == json.dumps(config, separators=(',', ':'))
        assert vector['sha256'] == hashlib.sha256(vector['json'].encode('utf-8')).hexdigest()

    manifest = read_json(CANDIDATE / 'base-inputs.json')
    source_checks = 0
    for label, tree in manifest['trees'].items():
        source = Path(tree['path'])
        for name in ['go.mod', 'go.sum']:
            assert sha(source / name) == tree[name], (label, name)
            source_checks += 1
        for relative, entry in manifest['files'].items():
            if label in entry['trees']:
                assert sha(source / relative) == entry['sha256'], (label, relative)
                source_checks += 1
        assert not (source / 'params/suicide_timelock_fix.go').exists()
        assert not (source / 'internal/recovery/f11_startup_recovery_test.go').exists()

    result = {'previous_manifest_files': previous, 'retained_overlay_input_checks': input_checks, 'selected_source_and_module_checks': source_checks, 'integration_top_level_passes': len(top), 'integration_subtest_passes': len(sub), 'genesis_equal_between_selections': True, 'genesis_matches_declared': False, 'initial_diagnostic_executed_tests': False}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
