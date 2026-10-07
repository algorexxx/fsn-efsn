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
    for name in ['restart-state-tests-2026-10-07', 'restart-state-rollback-followup-2026-10-07', CANDIDATE.name, 'restart-state-rollback-integration-2026-10-07']:
        directory = HERE.parent / name
        lines = (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
        for line in lines:
            expected, relative = line.split(None, 1)
            assert sha(directory / relative) == expected, (name, relative)
        previous[name] = len(lines)
    record = read_json(HERE / 'qualification/run.json')
    assert record['exit'] == 0 and record['uid'] == 1000
    for field in ['network_namespace', 'parent_network_namespace']:
        assert re.fullmatch(r'net:\[\d+\]', record[field])
    assert record['network_namespace'] != record['parent_network_namespace']
    assert len(record['links'].splitlines()) == 1 and record['links'].startswith('lo ') and 'DOWN' in record['links']
    assert record['candidate_manifest_sha256'] == sha(CANDIDATE / 'SHA256SUMS')
    overlay = read_json(HERE / 'qualification/overlay.json')['Replace']
    assert set(overlay) == set(record['overlay_input_sha256'])
    for logical, physical in overlay.items():
        retained = HERE.parent / physical.split('/docs/evidence/', 1)[1]
        assert sha(retained) == record['overlay_input_sha256'][logical], logical
    manifest = read_json(CANDIDATE / 'base-inputs.json')
    source = Path(record['source'])
    tree = manifest['trees']['recovery']
    assert str(source) == tree['path']
    source_checks = 0
    for name in ['go.mod', 'go.sum']:
        assert sha(source / name) == tree[name], name
        source_checks += 1
    for relative, entry in manifest['files'].items():
        if 'recovery' in entry['trees']:
            assert sha(source / relative) == entry['sha256'], relative
            source_checks += 1
    cli_inputs = read_json(HERE / 'cli-source-inputs.json')
    assert cli_inputs == record['cli_source_sha256']
    for relative, expected in cli_inputs.items():
        assert sha(source / relative) == expected, relative
        source_checks += 1
    assert not (source / 'cmd/fsn-recovery/f11_cli_configuration_test.go').exists()
    assert not (source / 'params/suicide_timelock_fix.go').exists()
    for name, vector in read_json(HERE / 'config-vectors.json').items():
        config = {'chainId': 32659, 'homesteadBlock': 0, 'eip150Hash': '0x' + '0' * 64, 'eip155Block': 0, 'eip158Block': 0, 'byzantiumBlock': 0, 'datong': {'period': 15}}
        if name != 'legacy':
            config['suicideTimeLockFixBlock'] = {'effective': 100, 'different': 101}[name]
        assert vector['json'] == json.dumps(config, separators=(',', ':'))
        assert vector['sha256'] == hashlib.sha256(vector['json'].encode('utf-8')).hexdigest()
    log = (HERE / 'qualification/tests.txt').read_text(encoding='utf-8')
    top = re.findall(r'^--- PASS: (\S+)', log, re.M)
    sub = re.findall(r'^    --- PASS: (\S+)', log, re.M)
    assert len(top) == 4 and len(sub) == 10 and 'FAIL' not in log
    result = {'previous_manifest_files': previous, 'retained_overlay_input_checks': len(overlay), 'recovery_source_and_module_checks': source_checks, 'top_level_passes': len(top), 'subtest_passes': len(sub)}
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
