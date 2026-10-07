from pathlib import Path
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    manifest = json.loads((HERE / 'base-inputs.json').read_text(encoding='utf-8'))
    run = json.loads((HERE / 'qualification-v2/run.json').read_text(encoding='utf-8'))
    first = json.loads((HERE / 'qualification/run.json').read_text(encoding='utf-8'))
    assert run['uid'] == 1000
    assert run['parent_network_namespace'].startswith('net:[')
    assert run['network_namespace'] != run['parent_network_namespace']
    assert [c['exit'] for c in run['commands']] == [0, 0, 0]
    assert sha(HERE / 'candidate-v2.patch') == run['patch_sha256']
    assert sha(HERE / 'candidate.patch') == first['patch_sha256']
    for name, expected in run['input_sha256'].items():
        assert sha(HERE / name) == expected, name
    for name, expected in first['input_sha256'].items():
        source = HERE / ('attempt-1-suicide_timelock_fix_test.go' if name == 'inputs/params/suicide_timelock_fix_test.go' else name)
        assert sha(source) == expected, name
    checks = {}
    for label, tree in manifest['trees'].items():
        base = Path(tree['path'])
        for name in ['go.mod', 'go.sum']:
            assert sha(base / name) == tree[name], (label, name)
        patch = []
        for name in sorted(run['input_sha256']):
            relative = name.removeprefix('inputs/')
            original = ''
            if relative in manifest['files']:
                entry = manifest['files'][relative]
                if label not in entry['trees']:
                    continue
                assert sha(base / relative) == entry['sha256'], (label, relative)
                original = (base / relative).read_text(encoding='utf-8')
            patch.extend(difflib.unified_diff(original.splitlines(keepends=True), (HERE / name).read_text(encoding='utf-8').splitlines(keepends=True), fromfile='a/' + relative if original else '/dev/null', tofile='b/' + relative))
        target = HERE / ('candidate-' + label + '.patch')
        data = ''.join(patch)
        if target.exists():
            assert target.read_text(encoding='utf-8') == data
        else:
            target.write_text(data, encoding='utf-8', newline='\n')
        check = subprocess.run(['git', 'apply', '--check', '--whitespace=error-all', str(target)], cwd=base, capture_output=True, text=True)
        checks[label] = {'exit': check.returncode, 'stdout': check.stdout, 'stderr': check.stderr, 'patch_sha256': sha(target)}
        assert check.returncode == 0, checks[label]
    candidate = (HERE / 'inputs/core/state/statedb.go').read_text(encoding='utf-8')
    inverse = candidate.replace('Suicide(addr common.Address, fixTimeLockJournal bool)', 'Suicide(addr common.Address)').replace('\n\t\t\tisTimeLock:          fixTimeLockJournal,', '')
    original = (Path(manifest['trees']['node']['path']) / 'core/state/statedb.go').read_text(encoding='utf-8')
    assert inverse == original, 'Unexpected state implementation changes'
    report = {'patch_apply_checks': checks, 'selected_inputs_unchanged': True, 'both_attempts_input_hashes_verified': True, 'statedb_delta_limited_to_parameter_and_discriminator': True, 'runtime_disposition': 'unselected', 'activation_height': None, 'state_evm_commit_or_block_tests_run': False}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
