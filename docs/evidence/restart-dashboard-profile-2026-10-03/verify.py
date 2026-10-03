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
assert record['base'] == '10c780ddeb15ffdeec4d671b58d9c85d7db2ca5b'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-profile.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines())
assert changed == {'wsclient/collect-snapshots.js', 'test/fixtures/collector-wire.cjs', 'test/fixtures/profile-wire-server.cjs', 'test/dashboard-profile.test.cjs', 'test/snapshot-collector.test.cjs', 'test/persistence.test.cjs', 'docs/dashboard-profile.md', 'docs/deployment-configuration.md'}
final = read(bundle / 'attempt-9/result.json')
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
profile_test = (dashboard / 'test/dashboard-profile.test.cjs').read_text(encoding='utf-8')
earlier_profile = profile_test.replace('await report(number, number === 1001 ? Array.from({ length: 50 }, (_, index) => busyBlock(1000 - index)) : undefined);', 'await report(number);').replace('assert.equal(histories.length, profile.nodes * (profile.succeeds ? 2 : 1));', 'assert.equal(histories.length, profile.nodes);')
earlier_profile_digest = hashlib.sha256(earlier_profile.encode('utf-8')).hexdigest()
contracts = read(bundle / 'contracts-1/result.json')
assert contracts['expected_outcome_passed']
assert [item['exit_code'] for item in contracts['results']] == [0, 0]
assert '# pass 161\n# fail 0\n' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 12\n# fail 0\n' in (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
for attempt in ['contracts-1', 'attempt-5', 'attempt-6', 'attempt-7', 'attempt-8']:
    run = read(bundle / attempt / 'result.json')
    for name, value in sources.items():
        expected = earlier_profile_digest if name == 'test/dashboard-profile.test.cjs' else value
        assert run['source_sha256'][name] == expected, (attempt, name)
baseline = read(bundle / 'baseline-observability/result.json')
assert baseline['exit_code'] == 1
assert '# pass 10\n# fail 2\n' in (bundle / 'baseline-observability/tests.stdout.txt').read_text(encoding='utf-8')
writer = 'wsclient/collect-snapshots.js'
baseline_writer = hashlib.sha256(subprocess.check_output(git + ['show', record['base'] + ':' + writer])).hexdigest()
assert baseline['source_sha256'][writer] == baseline_writer
assert baseline['source_sha256']['test/snapshot-collector.test.cjs'] == sources['test/snapshot-collector.test.cjs']
for index in range(1, 10):
    attempt = f'attempt-{index}'
    run = read(bundle / attempt / 'result.json')
    assert run['expected_outcome_passed'] is (index != 1)
    assert [item['exit_code'] for item in run['commands']] == [0, 0, 1 if index == 1 else 0, 0, 3]
    assert run['password_removed']
    assert run['node'] == 'v22.11.0' and run['postgres'] == 'postgres (PostgreSQL) 18.6'
    scratch = Path(run['scratch_directory'])
    assert not (scratch / 'password.txt').exists() and not (scratch / 'data/postmaster.pid').exists()
    if index < 5:
        assert run['source_sha256'][writer] == baseline_writer
    else:
        assert run['source_sha256'][writer] == sources[writer]
    expected_passes = 7 if index == 8 else 1
    if index != 1:
        assert f'# pass {expected_passes}\n# fail 0\n' in (bundle / attempt / 'profile.stdout.txt').read_text(encoding='utf-8')
for index, nodes, code, rejected in [(5, 2, 1009, 0), (6, 8, 1006, 1)]:
    data = read(bundle / f'attempt-{index}/profile.json')
    assert data['saves'] == [] and data['unavailableStatus'] == 503
    assert [item['code'] for item in data['closes']] == [code]
    assert data['errors'] == ['Collector connection closed unexpectedly']
    assert data['collector']['rejectedWrites'] == rejected
    assert data['collector']['cache'] == {'heights': 51, 'variants': 51, 'retainedArrays': 0}
    assert len(data['collector']['nodes']) == nodes
data = read(bundle / 'attempt-9/profile.json')
assert data['profile'] == {'nodes': 8, 'inputBytes': 4194304, 'outputBytes': 1048576, 'snapshotBytes': 1048576, 'succeeds': True}
assert data['errors'] == [] and [item['code'] for item in data['closes']] == [1000]
assert data['expiredStatus'] == 503
assert [(item['number'], item['historyBlocksPerReporter']) for item in data['batches']] == [(1000, 50), (1001, 50), (1002, 0), (1003, 0)]
assert [item['heights'] for item in data['saves']] == [[height] * 8 for height in range(1000, 1004)]
assert max(item['bytes'] for item in data['saves']) == 461205
assert data['http']['/nodes']['bytes'] == 483281
assert data['http']['/blocks']['bytes'] == 474540
assert data['http']['/charts']['bytes'] == 5700
collector = data['collector']
assert collector['rejectedWrites'] == 0 and collector['samples'] == 555
assert collector['cache'] == {'heights': 54, 'variants': 54, 'retainedArrays': 0}
assert [node['id'] for node in collector['nodes']] == ['profile-' + str(index) for index in range(8)]
assert all(node['height'] == 1003 and node['transactions'] == 714 and node['connected'] and all(isinstance(value, int) for value in node['reports'].values()) for node in collector['nodes'])
histories = [item['bytes'] for item in collector['records'] if item['direction'] == 'incoming' and item['event'] == 'history']
assert histories == [2811901] * 8 + [2811902] * 8
assert max(item['bytes'] for item in collector['records'] if item['direction'] == 'incoming' and item['event'] == 'block') == 56283
assert max(item['bytes'] for item in collector['records'] if item['direction'] == 'outgoing' and item['event'] == 'init') == 457084
assert collector['sampledPeaks']['rss'] == 250060800 and collector['sampledPeaks']['heapUsed'] == 63534400
assert collector['baseline']['rss'] == 133042176
for path in bundle.rglob('*.json'):
    assert 'synthetic-profile-credential-' not in path.read_text(encoding='utf-8-sig'), path
assert read(bundle / 'windows-process-cleanup.json') == {'remaining_test_processes': [], 'count': 0}
previous = bundle.parent / 'restart-dashboard-retention-2026-10-03'
main_sources = read(previous / 'attempt-6/efsn-source-sha256.json')
for name, value in main_sources.items():
    assert digest(root / name) == value
for value in record['runtime'].values():
    assert digest(Path(value['path'])) == value['sha256']
assert read(dashboard / 'node_modules/pg/package.json')['version'] == '8.23.1'
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'production_changes': [writer], 'dashboard_non_markdown_sources': len(sources), 'unchanged_efsn_go_and_module_sources': len(main_sources), 'new_regressions_failed_on_baseline': 2, 'contracts_passed': 161, 'wire_tests_passed': 12, 'database_scenarios_passed': 6, 'constrained_profiles_passed': 2, 'final_profile_nodes': 8, 'transactions_per_reported_block': 714, 'history_messages': 16, 'history_incoming_bytes': sorted(set(histories)), 'complete_snapshots_saved': len(data['saves']), 'largest_saved_snapshot_bytes': 461205, 'sampled_collector_rss_max_bytes': 250060800, 'first_profile_failure': 'Fixture expected onError; transport closed silently on preceding writer. Preserved and followed by close diagnostics and regression fix.', 'original_dashboard_preserved': True, 'efsn_unchanged': True, 'remaining_test_processes': 0, 'databases_stopped': 9, 'public_deployment_approved': False}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
