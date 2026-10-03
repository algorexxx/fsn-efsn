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
assert commit['base'] == 'b94e16cbf9527c42a4797e9590c407d7c521ec13'
assert subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base']
patch = (bundle / 'dashboard-presentation.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == commit['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']])
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit['dashboard_commit']]).decode().splitlines())
assert changed == {'react-frontend/src/Components/Main.js', 'test/efsn-telemetry.test.cjs', 'test/fixtures/efsn-browser.cjs', 'docs/actual-efsn-telemetry.md'}
integration = read(bundle / 'attempt-2/result.json')
assert integration['expected_outcome_passed'] and integration['password_file_removed']
assert [command['exit'] for command in integration['commands']] == [0, 0, 0, 0, 0, 3]
assert '# pass 1\n' in (bundle / 'attempt-2/persistence.txt').read_text(encoding='utf-8')
frontend = read(bundle / 'attempt-1/results.json')
assert [(item['name'], item['exit_code']) for item in frontend['results']] == [('react-tests', 0), ('build', 0)]
assert 'Tests:       8 passed, 8 total' in (bundle / 'attempt-1/react-tests.stderr.txt').read_text(encoding='utf-8')
assert 'Compiled successfully.' in (bundle / 'attempt-1/build.stdout.txt').read_text(encoding='utf-8')
assert not (bundle / 'attempt-1/build.stderr.txt').read_bytes()
sources = {name: value for name, value in integration['source_sha256'].items() if not name.endswith('.md')}
frontend_sources = read(bundle / 'attempt-1/source-sha256.json')
requests = ''.join(commit['dashboard_commit'] + ':' + name + '\n' for name in sources)
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode('utf-8'))
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert len(metadata) == 3 and metadata[1] == b'blob', name
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    assert frontend_sources[name] == value, name
    offset = end + size + 2
build_sources = read(bundle / 'attempt-1/build-sha256.json')
assert build_sources == integration['build_sha256']
for name, value in build_sources.items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
main_sources = read(bundle / 'attempt-2/efsn-source-sha256.json')
for name, value in main_sources.items():
    assert digest(root / name) == value, name
for name, artifact in commit['artifacts'].items():
    assert digest(Path(artifact['path'])) == artifact['sha256'], name
assert integration['binary_sha256'] == commit['artifacts']['efsn_test_binary']['sha256']
assert commit['artifacts']['linux_node_archive']['sha256'] == '83bf07dd343002a26211cf1fcd46a9d9534219aad42ee02847816940bf610a72'
assert not (Path(integration['scratch_directory']) / 'password.txt').exists()
assert not (Path(integration['scratch_directory']) / 'data/postmaster.pid').exists()
for platform in ['linux', 'windows']:
    assert read(bundle / (platform + '-process-cleanup.json')) == {'remaining_test_processes': [], 'count': 0}

comparison = read(bundle / 'attempt-2/comparison.json')
assert comparison['errors'] == []
assert comparison['captured'] == read(bundle / 'attempt-2/capture.json')
incoming = [entry for entry in comparison['captured']['records'] if entry['direction'] == 'incoming' and isinstance(entry['message'], dict) and 'emit' in entry['message']]
history = next(entry for entry in incoming if entry['message']['emit'][0] == 'history')
reported = history['message']['emit'][1]['history']
assert history['bytes'] == 66076 and len(reported) == 50
assert [block['number'] for block in reported] == list(range(59, 9, -1))
for report, direct in zip(reported, comparison['truth']['history']):
    for field in ['hash', 'parentHash', 'miner', 'stateRoot', 'transactionsRoot']:
        assert report[field].lower() == direct[field].lower()
    for field in ['number', 'timestamp', 'gasUsed', 'gasLimit', 'difficulty', 'totalDifficulty']:
        assert int(report[field]) == int(direct[field], 16)
    assert [tx['hash'] for tx in report['transactions']] == direct['transactions']
    assert len(direct['transactions']) == 10
    assert report['uncles'] == direct['uncles'] == []
node = json.loads(comparison['nodes']['body'][0]['stats'])
truth = comparison['truth']
assert node['stats']['block']['hash'] == comparison['ready']['head'] == truth['head']['hash']
assert len(truth['head']['transactions']) == 10
assert node['stats']['ticketNumber'] == truth['tickets'] == 2
assert node['stats']['myTicketNumber'] == truth['ownTickets'] == 2
assert node['stats']['peers'] == int(truth['peers'], 16) == 0
assert node['stats']['pending'] == int(truth['pending']['pending'], 16) == 0
assert node['stats']['mining'] is truth['mining'] is False
assert truth['syncing'] is False and node['stats']['syncing'] is True and node['stats']['uptime'] == 100
assert json.loads(comparison['charts']['body'][0]['charts'])['height'] == list(range(21, 61))
assert 'secret' not in next(entry for entry in incoming if entry['message']['emit'][0] == 'hello')['message']['emit'][1]
assert 'synthetic-node-a-credential' not in (bundle / 'attempt-2/comparison.json').read_text(encoding='utf-8')
for entry in incoming:
    if entry['message']['emit'][0] not in ['hello', 'ready']:
        assert len(json.dumps(entry['message'], separators=(',', ':'), ensure_ascii=False).encode('utf-8')) + 1 == entry['bytes']
browser = comparison['browser']
assert browser['errors'] == browser['foreignRequests'] == []
assert [entry['name'] for entry in browser['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert browser['checkpoints'][2]['directHead'] == truth['head']['hash']
assert 'Syncing' not in browser['checkpoints'][0]['headers'] and 'Reported Uptime' not in browser['checkpoints'][0]['headers']
assert 503 in browser['responses'] and browser['responses'][-1] == 200
assert read(bundle / 'attempt-2/browser-checkpoints.json') == {name: browser[name] for name in ['checkpoints', 'errors', 'foreignRequests', 'responses']}
for name in ['browser-actual.png', 'browser-expired.png']:
    assert (bundle / 'attempt-2' / name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
model = read(bundle / 'size-model.json')
assert [row['application_bytes'] for row in model['rows']] == [30926, 66076, 417126, 2811776]
assert model['retention_example']['all_variant_json_bytes'] == 1012212000

original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'dashboard_non_markdown_sources': len(sources), 'compiled_build_files': len(build_sources), 'efsn_go_and_module_sources': len(main_sources), 'react_dom_tests': 8, 'strict_build_passed': True, 'integration_tests': 1, 'browser_checkpoints': 4, 'browser_version': browser['browser'], 'compared_blocks': 51, 'rpc_requests': 59, 'history_bytes': history['bytes'], 'input_test_limit': comparison['limits']['messageBytes'], 'original_dashboard_preserved': True, 'efsn_reporter_unchanged': True, 'production_changes': ['react-frontend/src/Components/Main.js'], 'remaining_test_processes': 0, 'database_stopped': True}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
