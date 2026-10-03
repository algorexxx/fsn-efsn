import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = read(bundle / 'commit.json')
commit = record['dashboard_commit']
assert record['base'] == '9565d89e48110b68899053f6ffe09814d05ec74a'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-admission.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
production = ['lib/telemetry-info.js', 'lib/telemetry-report.js', 'server.js']
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines())
assert changed == set(production + ['docs/deployment-configuration.md', 'docs/metadata-admission.md', 'package.json', 'test/collector-output-wire.test.cjs', 'test/efsn-telemetry.test.cjs', 'test/fixtures/collector.cjs', 'test/fixtures/telemetry-report.cjs', 'test/fixtures/wire-client.cjs', 'test/metadata-admission-wire.test.cjs', 'test/metadata-admission.test.cjs'])
final = read(bundle / 'attempt-3/result.json')
sources = {name: value for name, value in final['source_sha256'].items() if not name.endswith('.md')}
tracked = subprocess.check_output(git + ['ls-tree', '-r', '--name-only', commit]).decode().splitlines()
assert set(sources) == {name for name in tracked if not name.endswith('.md')}
requests = ''.join(commit + ':' + name + '\n' for name in sources).encode('utf-8')
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests)
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert len(metadata) == 3 and metadata[1] == b'blob', name
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    assert digest(dashboard / name) == value, name
    offset = end + size + 2

contracts = read(bundle / 'contracts-1/result.json')
assert contracts['expected_outcome_passed']
assert [item['exit_code'] for item in contracts['results']] == [0, 0]
assert '# pass 167\n# fail 0\n' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 13\n# fail 0\n' in (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
for name, value in sources.items():
    if name != 'test/efsn-telemetry.test.cjs':
        assert contracts['source_sha256'][name] == value, name
assert 'EPERM' in (bundle / 'baseline/regression.stdout.txt').read_text(encoding='utf-8')
baseline = read(bundle / 'baseline-2/result.json')
assert baseline['results'][0]['exit_code'] == 1
assert '# tests 6\n# suites 0\n# pass 1\n# fail 5\n' in (bundle / 'baseline-2/regression.stdout.txt').read_text(encoding='utf-8')
for name in ['server.js', 'lib/telemetry-report.js']:
    parent_digest = hashlib.sha256(subprocess.check_output(git + ['show', record['base'] + ':' + name])).hexdigest()
    assert baseline['source_sha256'][name] == parent_digest
assert baseline['source_sha256']['test/metadata-admission.test.cjs'] == sources['test/metadata-admission.test.cjs']
assert 'lib/telemetry-info.js' not in baseline['source_sha256']

for index in range(1, 4):
    attempt = bundle / f'attempt-{index}'
    run = read(attempt / 'result.json')
    assert run['expected_outcome_passed'] is (index == 3)
    assert [item['exit'] for item in run['commands']] == [0, 0, 0, 0 if index == 3 else 1, 0, 3]
    assert run['password_file_removed']
    assert run['node'] == 'v22.11.0' and run['pg'] == '8.23.1' and run['postgres'] == 'postgres (PostgreSQL) 18.6'
    scratch = Path(run['scratch_directory'])
    assert not (scratch / 'password.txt').exists() and not (scratch / 'data/postmaster.pid').exists()
    for name, value in sources.items():
        if name != 'test/efsn-telemetry.test.cjs':
            assert run['source_sha256'][name] == value, (index, name)
    browser = read(attempt / 'browser-checkpoints.json')
    assert [item['name'] for item in browser['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
    assert browser['errors'] == browser['foreignRequests'] == []
    assert 503 in browser['responses'] and browser['responses'][-1] == 200
assert '# pass 1\n# fail 0\n' in (bundle / 'attempt-3/persistence.txt').read_text(encoding='utf-8')
failed_transport = read(bundle / 'attempt-2/transport.json')
refused = [item for item in failed_transport if item['kind'] == 'connectFailed']
assert len(refused) == 2 and all(item['code'] == 'ECONNREFUSED' and item['phase'] == 'startup' for item in refused)
assert any(item['kind'] == 'writer-error' and item['phase'] == 'cleanup' for item in failed_transport)
transport = read(bundle / 'attempt-3/transport.json')
assert not any(item['kind'] in ['writer-error', 'connectFailed'] for item in transport)
probes = [item for item in transport if item['kind'] == 'windows-port-readiness']
assert len(probes) == 5 and [item['ready'] for item in probes] == [False, False, False, False, True]
assert all(item['code'] == 'ECONNREFUSED' for item in probes[:-1])
assert probes[-1]['time'] - probes[0]['time'] == 441
assert [item['code'] for item in transport if item['kind'] == 'close'] == [1000, 1000]

data = read(bundle / 'attempt-3/comparison.json')
assert data['errors'] == []
assert data['limits'] == {'messageBytes': 131072, 'bufferedBytes': 262144, 'messagesPerSecond': 100, 'snapshotBytes': 65536}
assert data['nodes']['status'] == data['blocks']['status'] == data['charts']['status'] == 200
node = json.loads(data['nodes']['body'][0]['stats'])
assert node['stats']['block']['hash'] == data['truth']['head']['hash'] == data['ready']['head']
assert [tx['hash'] for tx in node['stats']['block']['transactions']] == data['truth']['head']['transactions']
assert json.loads(data['blocks']['body'][0]['blocks'])['transactions'] == node['stats']['block']['transactions']
assert json.loads(data['charts']['body'][0]['charts'])['transactions'] == [10] * 40
assert len(data['truth']['history']) == 50
incoming = [item for item in data['captured']['records'] if item['direction'] == 'incoming' and isinstance(item['message'], dict) and 'emit' in item['message']]
info = next(item['message']['emit'][1]['info'] for item in incoming if item['message']['emit'][0] == 'hello')
assert node['info'] == dict(info, name='node-a', ip='127.0.0.1')
assert len(json.dumps(info, ensure_ascii=False, separators=(',', ':')).encode()) == 201
ping_bytes = [len(json.dumps(item['message']['emit'][1]['clientTime'], separators=(',', ':')).encode()) for item in incoming if item['message']['emit'][0] == 'node-ping']
assert ping_bytes == [57, 58]
assert [item['bytes'] for item in incoming if item['message']['emit'][0] == 'history'] == [66076]

main_sources = read(bundle / 'attempt-3/efsn-source-sha256.json')
previous = read(bundle.parent / 'restart-dashboard-retention-2026-10-03/attempt-6/result.json')
assert main_sources == read(bundle.parent / 'restart-dashboard-retention-2026-10-03/attempt-6/efsn-source-sha256.json')
assert final['build_sha256'] == previous['build_sha256']
assert final['binary_sha256'] == previous['binary_sha256'] == digest(root / 'tmp/dashboard-presentation-tests')
for name, value in main_sources.items():
    assert digest(root / name) == value, name
for name, value in final['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
for value in record['runtime'].values():
    assert digest(Path(value['path'])) == value['sha256']
for platform in ['windows', 'linux']:
    assert read(bundle / f'{platform}-process-cleanup.json') == {'remaining_test_processes': [], 'count': 0}
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'production_changes': production, 'dashboard_non_markdown_sources': len(sources), 'unchanged_efsn_go_and_module_sources': len(main_sources), 'unchanged_frontend_build_files': len(final['build_sha256']), 'baseline_regressions_failed': 5, 'contracts_passed': 167, 'wire_tests_passed': 13, 'actual_efsn_browser_checkpoints_passed': 4, 'final_writer_errors': [], 'native_metadata_bytes': 201, 'native_ping_bytes': ping_bytes, 'windows_port_readiness_delay_ms': 441, 'preserved_failed_integrations': 2, 'stopped_databases': 3, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'efsn_unchanged': True, 'public_deployment_approved': False}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
