import hashlib
import json
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'baseline.json')
changed = sorted(name for name, value in baseline['source_sha256'].items() if digest(root / name) != value)
assert changed == ['cmd/fsn-observe/main.go'], changed
results = {}
for platform, log_name in [('windows', 'tests.txt'), ('linux', 'tests-race.txt')]:
    directory = bundle / 'attempt-1' / platform
    for name in ['test-exit.txt', 'build-exit.txt']:
        assert (directory / name).read_text(encoding='utf-8').strip() == '0'
    log = (directory / log_name).read_text(encoding='utf-8')
    assert 'FAIL' not in log
    for name in ['TestHistoryCheckBoundariesAndUnresolvedState', 'TestHistoryCheckRequiresExplicitBounds', 'TestHistoryCheckFailedAppendAndReviewCannotRenewCollection', 'TestCommandHistoryCheck/in-process', 'TestCommandHistoryCheck/binary']:
        assert '--- PASS: ' + name + ' (' in log, name
    if platform == 'windows':
        sources = read(directory / 'sources.json')
    else:
        sources = {name: value for value, name in (line.split('  ', 1) for line in (directory / 'sources.sha256').read_text(encoding='utf-8').splitlines())}
        network = (directory / 'network.txt').read_text(encoding='utf-8').splitlines()
        assert len(network) == 1 and network[0].split()[0] == 'lo'
    for name, value in sources.items():
        assert digest(root / name) == value, name
    for mode in ['in-process', 'binary']:
        commands = read(directory / ('commands-' + mode + '.json'))
        assert len(commands) == 24
        for index, exit_code, problems in [(0, 1, ['collection_missing']), (4, 0, []), (5, 1, ['collection_stale']), (6, 1, ['history_headroom_low'])]:
            assert commands[index]['Exit'] == exit_code
            check = json.loads(commands[index]['Output'])
            assert check['Problems'] == problems and check['Version'] == 1
            assert check['History']['Sequence'] == (0 if index == 0 else 1)
        assert commands[1]['Exit'] == 0
        assert commands[2]['Exit'] == 1 and commands[2]['Output'] == ''
        assert commands[3]['Exit'] == 0 and commands[-1]['Exit'] == 0
        assert commands[3]['Output'] == commands[-1]['Output']
        for command in commands[7:-1]:
            assert command['Exit'] == 1 and command['Output'] == ''
        exported = [json.loads(line) for line in commands[3]['Output'].splitlines()]
        assert len(exported) == 2 and exported[1]['Sequence'] == 1
        assert exported[0]['Metadata']['MaxBytes'] == 65536
        assert exported[1]['Report']['Nodes'][0]['Role'] == 'retired'
    results[platform] = {'suite': 'passed', 'build': 'passed', 'captured_command_invocations': 48}

record = {
    'verified': True,
    'baseline': baseline['baseline'],
    'changed_existing_source_files': changed,
    'unchanged_existing_source_files': len(baseline['source_sha256']) - len(changed),
    'results': results,
    'node_or_consensus_changes': False,
    'provider_selected': False,
    'external_messages_sent': False,
    'external_delivery_or_host_loss_tested': False,
    'production_thresholds_selected': False,
}
(bundle / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
