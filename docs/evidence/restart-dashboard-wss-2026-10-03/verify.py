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
assert record['base'] == '4ca1f59bb273569e5b82a1390e93b36e1fdd4b01'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-wss.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
assert len(changed) == 10 and all(name.startswith(('test/', 'docs/')) for name in changed)
final = read(bundle / 'attempt-4/result.json')
sources = final['source_sha256']
tracked = subprocess.check_output(git + ['ls-tree', '-r', '--name-only', commit]).decode().splitlines()
assert set(sources) == {name for name in tracked if not name.endswith('.md')}
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=''.join(commit + ':' + name + '\n' for name in sources).encode())
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert metadata[1] == b'blob'
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    assert digest(dashboard / name) == value, name
    offset = end + size + 2
assert final['passed'] and final['sources_unchanged_during_run']
assert final['runner_sha256'] == digest(bundle / 'run.py')
for index in range(1, 5):
    run = read(bundle / f'attempt-{index}/result.json')
    assert run['passed'] is (index == 4)
    assert run['password_removed'] and run['private_removed'] and run['postgres_pid_absent']
    assert not (Path(run['scratch_directory']) / 'password.txt').exists()
    commands = {item['name']: item['exit'] for item in run['commands']}
    if index == 1:
        assert commands['ca'] == 1 and 'start' not in commands
    else:
        assert commands['actual-wss'] == (0 if index == 4 else 1)
        assert commands['stop'] == 0 and commands['stopped-status'] == 3
    assert run['runtime_sha256'] == final['runtime_sha256']
    assert run['build_sha256'] == final['build_sha256']
    assert run['efsn_source_sha256'] == final['efsn_source_sha256']
for name, value in final['runtime_sha256'].items():
    assert digest(root / name) == value, name
assert digest(Path('C:/Program Files/nodejs/node.exe')) == final['windows_node_sha256']
previous = bundle.parent / 'restart-dashboard-enrollment-2026-10-03/attempt-4'
previous_go = read(previous / 'efsn-source-sha256.json')
go_changes = [name for name, value in final['efsn_source_sha256'].items() if previous_go[name] != value]
assert go_changes == ['tests/restart/dashboard_telemetry_linux_test.go']
for name, value in final['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
assert record['go_fixture_sha256'] == final['efsn_source_sha256'][go_changes[0]]
assert final['build_sha256'] == read(previous / 'result.json')['build_sha256']
for name, value in final['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
contracts = read(bundle / 'contracts-1/result.json')
assert contracts['source_sha256'] == sources
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
assert '# pass 173\n# fail 0\n' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 13\n# fail 0\n' in (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
plain = read(bundle / 'attempt-5/result.json')
assert plain['expected_outcome_passed'] and plain['password_file_removed']
assert plain['binary_sha256'] == final['runtime_sha256']['tmp/dashboard-tls-tests']
assert {name: value for name, value in plain['source_sha256'].items() if not name.endswith('.md')} == sources
assert plain['build_sha256'] == final['build_sha256']
assert not (Path(plain['scratch_directory']) / 'data/postmaster.pid').exists()
assert not (Path(plain['scratch_directory']) / 'password.txt').exists()
for index in [4, 5]:
    data = read(bundle / f'attempt-{index}/comparison.json')
    assert data['tls'] is (index == 4)
    assert data['errors'] == [] and len(data['truth']['history']) == 50
    assert data['truth']['mining'] is False and int(data['truth']['peers'], 16) == 0
    assert [item['name'] for item in data['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
    assert data['browser']['errors'] == data['browser']['foreignRequests'] == []
    assert 503 in data['browser']['responses'] and data['browser']['responses'][-1] == 200
    for response in [data['nodes'], data['blocks'], data['charts']]:
        assert response['status'] == 200
        if index == 4:
            assert response['tls']['authorized'] and response['tls']['protocol'] == 'TLSv1.3'
    node = json.loads(data['nodes']['body'][0]['stats'])
    assert node['stats']['block']['hash'] == data['truth']['head']['hash'] == data['ready']['head']
    assert [tx['hash'] for tx in node['stats']['block']['transactions']] == data['truth']['head']['transactions']
    assert json.loads(data['blocks']['body'][0]['blocks'])['transactions'] == node['stats']['block']['transactions']
    assert json.loads(data['charts']['body'][0]['charts'])['transactions'] == [10] * 40
data = read(bundle / 'attempt-4/comparison.json')
assert data['browser']['security']['protocol'] == 'TLS 1.3'
assert 'ERR_CERT_AUTHORITY_INVALID' in data['browser']['certificateError']
assert data['browser']['certificateSpki'] == final['certificate_spki']
writer = data['finalCaptured']['writer']
assert writer['errors'] == [] and len(writer['saves']) == 15
assert max(item['bytes'] for item in writer['saves']) == 6958
assert [item['kind'] for item in writer['transport']] == ['connect', 'open', 'close', 'connect', 'open', 'close']
assert [item['code'] for item in writer['transport'] if item['kind'] == 'close'] == [1000, 1000]
assert read(bundle / 'attempt-4/proxy/process.json')['result'] == [0, None]
skew = read(bundle / 'attempt-2/api-initial.json')
row = skew['nodes']['body'][0]
assert row['reportValidForMs'] == {'block': None, 'stats': None, 'pending': None}
assert '# pass 0\n# fail 1\n' in (bundle / 'attempt-3/actual-wss.stdout.txt').read_text(encoding='utf-8')
assert 'ERR_IPC_CHANNEL_CLOSED' in (bundle / 'attempt-3/actual-wss.stdout.txt').read_text(encoding='utf-8')
assert read(bundle / 'linux-process-cleanup.json')['count'] == 0
assert read(bundle / 'windows-process-cleanup.json')['count'] == 0
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'production_application_changes': 0, 'dashboard_non_markdown_sources': len(sources), 'efsn_fixture_changes': go_changes, 'unchanged_efsn_go_and_module_sources': len(previous_go) - 1, 'unchanged_frontend_build_files': len(final['build_sha256']), 'contracts_passed': 173, 'wire_tests_passed': 13, 'actual_wss_browser_checkpoints': 4, 'plain_loopback_browser_checkpoints': 4, 'stopped_databases': 4, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'mining_outage_tested': False, 'public_deployment_approved': False}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
