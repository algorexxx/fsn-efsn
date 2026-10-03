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
assert record['base'] == 'ef473d792e38cfdf79e2abc798dd1045696fddf5'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-enrollment.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
production = ['lib/collection.js', 'lib/deployment-config.js', 'lib/telemetry-credentials.js', 'lib/telemetry-head.js', 'lib/telemetry-info.js', 'server.js']
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines())
assert len(changed) == 20
assert {name for name in changed if not name.startswith(('docs/', 'test/')) and name != 'package.json'} == set(production)
final = read(bundle / 'attempt-5/result.json')
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

fixture = 'test/fixtures/budget-report.cjs'
ascii_fixture = (dashboard / fixture).read_text(encoding='utf-8').replace("    const remaining = 2048 - Buffer.byteLength(JSON.stringify(value));\n    value.node += '\\u2028'.repeat(Math.floor(remaining / 3)) + 'x'.repeat(remaining % 3);", "    value.node += 'x'.repeat(2048 - Buffer.byteLength(JSON.stringify(value)));")
ascii_hash = hashlib.sha256(ascii_fixture.encode()).hexdigest()
assert ascii_hash != sources[fixture]
profile = 'test/enrollment-profile.test.cjs'
initial_profile = (dashboard / profile).read_text(encoding='utf-8').replace('assert.deepEqual(row.reportValidForMs, { block: 0, stats: 0, pending: 0 });', 'assert.deepEqual(row.reportValidForMs, { block: null, stats: null, pending: null });')
initial_hash = hashlib.sha256(initial_profile.encode()).hexdigest()
assert initial_hash != sources[profile]
contracts = read(bundle / 'contracts-1/result.json')
assert contracts['expected_outcome_passed'] and [item['exit_code'] for item in contracts['results']] == [0, 0]
assert '# pass 173\n# fail 0\n' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 13\n# fail 0\n' in (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
assert profile not in contracts['source_sha256']
for name, value in sources.items():
    if name != profile:
        assert contracts['source_sha256'][name] == (ascii_hash if name == fixture else value), name
baseline = read(bundle / 'baseline/result.json')
assert baseline['results'][0]['exit_code'] == 1
assert '# tests 6\n# suites 0\n# pass 0\n# fail 6\n' in (bundle / 'baseline/regression.stdout.txt').read_text(encoding='utf-8')
for name in production:
    if name == 'lib/telemetry-head.js':
        assert name not in baseline['source_sha256']
    else:
        assert baseline['source_sha256'][name] == hashlib.sha256(subprocess.check_output(git + ['show', record['base'] + ':' + name])).hexdigest()
assert baseline['source_sha256']['test/head-budget.test.cjs'] == sources['test/head-budget.test.cjs']

for index in range(1, 6):
    attempt = bundle / f'attempt-{index}'
    run = read(attempt / 'result.json')
    assert run['expected_outcome_passed'] is (index != 1)
    if index == 4:
        assert [item['exit'] for item in run['commands']] == [0, 0, 0, 0, 0, 3]
        assert run['password_file_removed']
    else:
        assert [item['exit_code'] for item in run['commands']] == [0, 0, 1 if index == 1 else 0, 0, 3]
        assert run['password_removed']
    assert run['node'] == 'v22.11.0' and run['postgres'] == 'postgres (PostgreSQL) 18.6'
    scratch = Path(run['scratch_directory'])
    assert not (scratch / 'password.txt').exists() and not (scratch / 'data/postmaster.pid').exists()
    for name, value in sources.items():
        expected = ascii_hash if name == fixture and index < 5 else initial_hash if name == profile and index == 1 else value
        assert run['source_sha256'][name] == expected, (index, name)
    if index != 1:
        log = attempt / ('persistence.txt' if index == 4 else 'profile.stdout.txt')
        assert '# pass 1\n# fail 0\n' in log.read_text(encoding='utf-8')

first_log = (bundle / 'attempt-1/profile.stdout.txt').read_text(encoding='utf-8')
assert 'AssertionError' in first_log
assert 'block: 0' in first_log and 'block: ~' in first_log
for index in [2, 5]:
    data = read(bundle / f'attempt-{index}/enrollment.json')
    assert data['headBytes'] == 65536 and data['metadataBytes'] == 2048 and data['ids'] == 8
    assert data['errors'] == []
    assert data['saves'][0] == {'bytes': 554917, 'connected': 0}
    assert data['saves'][-1]['connected'] == 1
    assert len(data['inactive']['nodes']) == len(data['rotated']['nodes']) == 8
    assert all(not node['connected'] and node['transactions'] == 714 for node in data['inactive']['nodes'])
    assert sum(node['connected'] for node in data['rotated']['nodes']) == 1
    assert data['rotated']['rejectedWrites'] == data['rotated']['cache']['retainedArrays'] == 0
    assert data['http'] == {'/nodes': {'bytes': 589075}, '/blocks': {'bytes': 549897}}
data = read(bundle / 'attempt-5/enrollment.json')
records = data['rotated']['records']
inventory = max(item['bytes'] for item in records if item['direction'] == 'outgoing' and item['event'] == 'init')
charts = max(item['bytes'] for item in records if item['direction'] == 'outgoing' and item['event'] == 'charts')
assert inventory == 561635 and charts == 8798
assert [item['bytes'] for item in records if item['direction'] == 'incoming' and item['event'] == 'history'] == [3276956]
assert inventory + charts < 8 * (65536 + 8192) + 32768 == 622592 < 1048576
aligned = read(bundle / 'attempt-3/profile.json')
assert aligned['errors'] == [] and aligned['expiredStatus'] == 503
assert [save['heights'] for save in aligned['saves']] == [[number] * 8 for number in range(1000, 1004)]
assert max(save['bytes'] for save in aligned['saves']) == 461244
assert aligned['collector']['rejectedWrites'] == 0

actual = read(bundle / 'attempt-4/comparison.json')
assert actual['errors'] == [] and len(actual['truth']['history']) == 50
assert [item['name'] for item in actual['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert actual['browser']['errors'] == actual['browser']['foreignRequests'] == []
assert actual['nodes']['status'] == actual['blocks']['status'] == actual['charts']['status'] == 200
node = json.loads(actual['nodes']['body'][0]['stats'])
assert node['stats']['block']['hash'] == actual['truth']['head']['hash'] == actual['ready']['head']
assert [tx['hash'] for tx in node['stats']['block']['transactions']] == actual['truth']['head']['transactions']
assert json.loads(actual['blocks']['body'][0]['blocks'])['transactions'] == node['stats']['block']['transactions']
assert json.loads(actual['charts']['body'][0]['charts'])['transactions'] == [10] * 40
main_sources = read(bundle / 'attempt-4/efsn-source-sha256.json')
previous_bundle = bundle.parent / 'restart-dashboard-admission-2026-10-03'
previous = read(previous_bundle / 'attempt-3/result.json')
actual_run = read(bundle / 'attempt-4/result.json')
assert main_sources == read(previous_bundle / 'attempt-3/efsn-source-sha256.json')
assert actual_run['build_sha256'] == previous['build_sha256']
assert actual_run['binary_sha256'] == previous['binary_sha256'] == digest(root / 'tmp/dashboard-presentation-tests')
for name, value in main_sources.items():
    assert digest(root / name) == value
for name, value in actual_run['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
for name, value in read(bundle / 'dependency-source-sha256.json').items():
    assert digest(dashboard / name) == value
for value in record['runtime'].values():
    assert digest(Path(value['path'])) == value['sha256']
for platform in ['windows', 'linux']:
    assert read(bundle / f'{platform}-process-cleanup.json') == {'remaining_test_processes': [], 'count': 0}
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
assert digest(root / 'ethstats/ethstats.go') == original['efsn_ethstats_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'production_changes': production, 'dashboard_non_markdown_sources': len(sources), 'unchanged_efsn_go_and_module_sources': len(main_sources), 'unchanged_frontend_build_files': len(actual_run['build_sha256']), 'baseline_regressions_failed': 6, 'contracts_passed': 173, 'wire_tests_passed': 13, 'enrolled_boundary_nodes': 8, 'head_bytes': 65536, 'metadata_bytes': 2048, 'largest_unicode_inventory_bytes': inventory, 'largest_boundary_snapshot_bytes': 554917, 'actual_efsn_browser_checkpoints_passed': 4, 'stopped_databases': 5, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'efsn_unchanged': True, 'public_deployment_approved': False}
(bundle / 'verification.json').write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
print(json.dumps(result, indent=2))
