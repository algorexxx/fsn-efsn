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


commit = read(bundle / 'commit.json')
assert commit['base'] == '57d77791acc3af21160697efb45aa854f0e66066'
assert subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base']
patch = (bundle / 'dashboard-telemetry.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == commit['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']])
assert set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit['dashboard_commit']]).decode().splitlines()) == {'test/efsn-telemetry.test.cjs', 'test/fixtures/efsn-wire-server.cjs', 'test/fixtures/efsn-wsl-server.cjs', 'docs/actual-efsn-telemetry.md'}
accepted = read(bundle / 'attempt-3/result.json')
assert accepted['expected_outcome_passed']
assert [command['exit'] for command in accepted['commands']] == [0, 0, 0, 0, 0, 3]
assert '# pass 1\n' in (bundle / 'attempt-3/persistence.txt').read_text(encoding='utf-8')
sources = {name: value for name, value in accepted['source_sha256'].items() if not name.endswith('.md')}
requests = ''.join(commit['dashboard_commit'] + ':' + name + '\n' for name in sources)
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode())
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert len(metadata) == 3 and metadata[1] == b'blob', name
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    offset = end + size + 2
main_sources = read(bundle / 'attempt-3/efsn-source-sha256.json')
for name, value in main_sources.items():
    assert digest(root / name) == value, name
assert 'tests/restart/dashboard_telemetry_linux_test.go' in main_sources
assert accepted['binary_sha256'] == commit['artifacts']['efsn_test_binary']['sha256']
for artifact in commit['artifacts'].values():
    assert digest(Path(artifact['path'])) == artifact['sha256']
assert commit['artifacts']['linux_node_archive']['sha256'] == '83bf07dd343002a26211cf1fcd46a9d9534219aad42ee02847816940bf610a72'
assert '83bf07dd343002a26211cf1fcd46a9d9534219aad42ee02847816940bf610a72  node-v22.11.0-linux-x64.tar.xz' in (bundle / 'node-shasums.txt').read_text()
for attempt in ['attempt-1', 'attempt-2', 'attempt-3']:
    result = read(bundle / attempt / 'result.json')
    assert result['password_file_removed']
    assert result['commands'][-2]['exit'] == 0 and result['commands'][-1]['exit'] == 3
    assert not (Path(result['scratch_directory']) / 'password.txt').exists()
    assert not (Path(result['scratch_directory']) / 'data/postmaster.pid').exists()
for platform in ['linux', 'windows']:
    cleanup = read(bundle / (platform + '-process-cleanup.json'))
    assert cleanup == {'remaining_test_processes': [], 'count': 0}

comparison = read(bundle / 'attempt-3/comparison.json')
assert comparison['errors'] == []
assert comparison['captured'] == read(bundle / 'attempt-3/capture.json')
incoming = [entry for entry in comparison['captured']['records'] if entry['direction'] == 'incoming' and isinstance(entry['message'], dict) and 'emit' in entry['message']]
history = next(entry for entry in incoming if entry['message']['emit'][0] == 'history')
reported = history['message']['emit'][1]['history']
assert history['bytes'] == 30926 and len(reported) == 50
assert [block['number'] for block in reported] == list(range(59, 9, -1))
for report, direct in zip(reported, comparison['truth']['history']):
    for field in ['hash', 'parentHash', 'miner', 'stateRoot', 'transactionsRoot']:
        assert report[field].lower() == direct[field].lower()
    for field in ['number', 'timestamp', 'gasUsed', 'gasLimit', 'difficulty', 'totalDifficulty']:
        assert int(report[field]) == int(direct[field], 16)
    assert [tx['hash'] for tx in report['transactions']] == direct['transactions']
    assert report['uncles'] == direct['uncles'] == []
node = json.loads(comparison['nodes']['body'][0]['stats'])
truth = comparison['truth']
assert node['stats']['block']['hash'] == comparison['ready']['head'] == truth['head']['hash']
assert node['stats']['ticketNumber'] == truth['tickets'] == 2
assert node['stats']['myTicketNumber'] == truth['ownTickets'] == 2
assert node['stats']['peers'] == int(truth['peers'], 16) == 0
assert node['stats']['pending'] == int(truth['pending']['pending'], 16) == 0
assert node['stats']['mining'] is truth['mining'] is False
assert truth['syncing'] is False and node['stats']['syncing'] is True and node['stats']['uptime'] == 100
assert node['connected'] is True and all(value > 0 for value in comparison['nodes']['body'][0]['reportValidForMs'].values())
assert json.loads(comparison['charts']['body'][0]['charts'])['height'] == list(range(21, 61))
hello = next(entry for entry in incoming if entry['message']['emit'][0] == 'hello')
assert 'secret' not in hello['message']['emit'][1]
assert 'synthetic-node-a-credential' not in (bundle / 'attempt-3/comparison.json').read_text()
for entry in incoming:
    if entry['message']['emit'][0] not in ['hello', 'ready']:
        assert len(json.dumps(entry['message'], separators=(',', ':'), ensure_ascii=False).encode()) + 1 == entry['bytes']
hash_entry_bytes = len(json.dumps(reported[0]['transactions'][0], separators=(',', ':')).encode()) + 1
assert hash_entry_bytes == 78
busy_history = history['bytes'] + 450 * hash_entry_bytes
assert busy_history == 66026 and busy_history > comparison['limits']['messageBytes']

original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'dashboard_non_markdown_sources': len(sources), 'efsn_go_and_module_sources': len(main_sources), 'integration_tests': 1, 'compared_blocks': 51, 'rpc_requests': 58, 'history_bytes': history['bytes'], 'offline_ten_transactions_per_block_history_bytes': busy_history, 'collector_memory_observation': comparison['captured']['memory'], 'original_dashboard_preserved': True, 'production_changes': 0, 'remaining_test_processes': 0, 'all_three_databases_stopped': True}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
print(json.dumps(result, indent=2))
