import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
previous = bundle.parent / 'restart-dashboard-presentation-2026-10-03'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = read(bundle / 'commit.json')
commit = record['dashboard_commit']
assert record['base'] == 'e69fe7982049dad5621871d6d96f380624e148af'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-retention.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines())
production = {'lib/chart-block.js', 'lib/collection.js', 'lib/history.js', 'lib/telemetry-report.js'}
assert changed == production | {'package.json', 'docs/report-validation-and-retention.md', 'test/collector-input-wire.test.cjs', 'test/efsn-telemetry.test.cjs', 'test/history-wire.test.cjs', 'test/history.test.cjs', 'test/persistence.test.cjs', 'test/report-freshness-wire.test.cjs', 'test/report-freshness.test.cjs', 'test/fixtures/telemetry-report.cjs', 'test/telemetry-report.test.cjs'}
baseline = read(bundle / 'attempt-1/result.json')
contracts = read(bundle / 'attempt-3/result.json')
assert baseline['expected_outcome_passed'] and contracts['expected_outcome_passed']
assert '# pass 0\n# fail 8\n' in (bundle / 'attempt-1/regression.stdout.txt').read_text(encoding='utf-8')
assert [item['exit_code'] for item in contracts['results']] == [0, 0]
assert '# pass 159\n# fail 0\n' in (bundle / 'attempt-3/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 12\n# fail 0\n' in (bundle / 'attempt-3/test-wire.stdout.txt').read_text(encoding='utf-8')
for name in ['test/telemetry-report.test.cjs', 'test/fixtures/telemetry-report.cjs']:
    assert baseline['source_sha256'][name] == contracts['source_sha256'][name]
assert not read(bundle / 'attempt-2/result.json')['expected_outcome_passed']
assert not read(bundle / 'attempt-5/result.json')['expected_outcome_passed']
assert 'efsn-telemetry.test.cjs:138:12' in (bundle / 'attempt-5/persistence.txt').read_text(encoding='utf-8')
integration = read(bundle / 'attempt-6/result.json')
persistence = read(bundle / 'attempt-4/result.json')
for attempt, expected in [('attempt-4', 7), ('attempt-6', 1)]:
    result = read(bundle / attempt / 'result.json')
    assert result['expected_outcome_passed'] and result['password_file_removed']
    assert [item['exit'] for item in result['commands']] == [0, 0, 0, 0, 0, 3]
    assert f'# pass {expected}\n# fail 0\n' in (bundle / attempt / 'persistence.txt').read_text(encoding='utf-8')
for attempt in ['attempt-4', 'attempt-5', 'attempt-6']:
    scratch = Path(read(bundle / attempt / 'result.json')['scratch_directory'])
    assert not (scratch / 'password.txt').exists()
    assert not (scratch / 'data/postmaster.pid').exists()
sources = {name: value for name, value in integration['source_sha256'].items() if not name.endswith('.md')}
tracked = subprocess.check_output(git + ['ls-tree', '-r', '--name-only', commit]).decode().splitlines()
assert set(sources) == {name for name in tracked if not name.endswith('.md')}
requests = ''.join(commit + ':' + name + '\n' for name in sources)
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode('utf-8'))
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert len(metadata) == 3 and metadata[1] == b'blob', name
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    assert digest(dashboard / name) == value, name
    if name != 'test/efsn-telemetry.test.cjs':
        assert contracts['source_sha256'][name] == persistence['source_sha256'][name] == value, name
    offset = end + size + 2
build = read(previous / 'attempt-1/build-sha256.json')
assert build == integration['build_sha256']
frontend_sources = read(previous / 'attempt-1/source-sha256.json')
for name, value in sources.items():
    if name.startswith('react-frontend/'):
        assert frontend_sources[name] == value
for name, value in build.items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
main_sources = read(bundle / 'attempt-6/efsn-source-sha256.json')
assert main_sources == read(previous / 'attempt-2/efsn-source-sha256.json')
for name, value in main_sources.items():
    assert digest(root / name) == value
for artifact in record['artifacts'].values():
    assert digest(Path(artifact['path'])) == artifact['sha256']
assert integration['binary_sha256'] == record['artifacts']['efsn_test_binary']['sha256']
comparison = read(bundle / 'attempt-6/comparison.json')
assert comparison['errors'] == []
assert comparison['captured'] == read(bundle / 'attempt-6/capture.json')
incoming = [entry for entry in comparison['captured']['records'] if entry['direction'] == 'incoming' and isinstance(entry['message'], dict) and 'emit' in entry['message']]
history = next(entry for entry in incoming if entry['message']['emit'][0] == 'history')
reports = history['message']['emit'][1]['history']
assert history['bytes'] == 66076 and len(reports) == 50
assert [report['number'] for report in reports] == list(range(59, 9, -1))
node = json.loads(comparison['nodes']['body'][0]['stats'])
blocks = json.loads(comparison['blocks']['body'][0]['blocks'])
assert comparison['blocks']['status'] == 200
for report, direct in [(node['stats']['block'], comparison['truth']['head']), (blocks, comparison['truth']['head']), *zip(reports, comparison['truth']['history'])]:
    for field in ['hash', 'parentHash', 'miner', 'transactionsRoot', 'stateRoot']:
        assert report[field].lower() == direct[field].lower()
    for field in ['number', 'timestamp', 'gasUsed', 'gasLimit', 'difficulty', 'totalDifficulty']:
        assert int(report[field]) == int(direct[field], 16)
    assert [tx['hash'] for tx in report['transactions']] == direct['transactions']
    assert len(direct['transactions']) == 10
    assert report['uncles'] == direct['uncles'] == []
truth = comparison['truth']
assert node['stats']['ticketNumber'] == truth['tickets'] == 2
assert node['stats']['myTicketNumber'] == truth['ownTickets'] == 2
assert node['stats']['mining'] is truth['mining'] is False
assert node['stats']['peers'] == int(truth['peers'], 16) == 0
assert node['stats']['pending'] == int(truth['pending']['pending'], 16) == 0
assert node['stats']['syncing'] is True and truth['syncing'] is False and node['stats']['uptime'] == 100
charts = json.loads(comparison['charts']['body'][0]['charts'])
assert charts['height'] == list(range(21, 61)) and charts['transactions'] == [10] * 40
initial = read(bundle / 'attempt-6/api-initial.json')
assert initial['nodes'] == comparison['nodes'] and initial['blocks'] == comparison['blocks']
assert all(value > 0 for value in initial['nodes']['body'][0]['reportValidForMs'].values())
for filename in ['api-initial.json', 'capture.json', 'comparison.json']:
    assert 'synthetic-node-a-credential' not in (bundle / 'attempt-6' / filename).read_text(encoding='utf-8')
browser = comparison['browser']
assert browser['errors'] == browser['foreignRequests'] == []
assert [entry['name'] for entry in browser['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert browser['checkpoints'][2]['directHead'] == truth['head']['hash']
assert 503 in browser['responses'] and browser['responses'][-1] == 200
assert read(bundle / 'attempt-6/browser-checkpoints.json') == {name: browser[name] for name in ['checkpoints', 'errors', 'foreignRequests', 'responses']}
for name in ['browser-actual.png', 'browser-expired.png']:
    assert (bundle / 'attempt-6' / name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
measurement = read(bundle / 'cache-measurement.json')
assert [row['transactionsPerBlock'] for row in measurement['rows']] == [1, 714]
assert [row['serializedCacheBytes'] for row in measurement['rows']] == [14195884, 14235884]
for row in measurement['rows']:
    assert row['heights'] == 2000 and row['identities'] == 8 and row['retainedForks'] == 18000
    assert 0 < row['heapDeltaBytes'] < 20 * 1024 * 1024
    assert row['afterEviction']['heapUsed'] < row['retained']['heapUsed']
for platform in ['linux', 'windows']:
    assert read(bundle / (platform + '-process-cleanup.json')) == {'remaining_test_processes': [], 'count': 0}
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'production_changes': sorted(production), 'dashboard_non_markdown_sources': len(sources), 'unchanged_compiled_build_files': len(build), 'unchanged_efsn_go_and_module_sources': len(main_sources), 'baseline_regressions_failed': 8, 'contracts_passed': 159, 'wire_tests_passed': 12, 'database_scenarios_passed': 6, 'actual_node_integration_passed': True, 'browser_checkpoints': 4, 'compared_distinct_blocks': 51, 'current_head_api_routes_checked': ['/nodes', '/blocks'], 'history_bytes': history['bytes'], 'cache_retained_forks': 18000, 'cache_json_bytes_714_transactions': 14235884, 'first_actual_attempt_freshness_failure_cause': 'unproven; preserved with later readiness/diagnostic improvement', 'original_dashboard_preserved': True, 'efsn_reporter_unchanged': True, 'remaining_test_processes': 0, 'databases_stopped': 3}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
