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
assert record['base'] == 'd9dfa96b8323db2621f2d7e41a70304c2f1b7415'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-mining.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
assert sorted(changed) == ['docs/mining-outage-acceptance.md', 'test/efsn-mining-outage.test.cjs', 'test/fixtures/collector-wire.cjs']
final = read(bundle / 'attempt-3/result.json')
baseline = read(bundle / 'attempt-2/result.json')
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
for name in ['attempt-1', 'attempt-2', 'attempt-3', 'stationary-1', 'stationary-2']:
    run = read(bundle / name / 'result.json')
    fixed = name in ['attempt-3', 'stationary-2']
    assert run['passed'] is (name != 'attempt-1')
    assert run['password_removed'] and run['private_removed'] and run['postgres_pid_absent']
    assert not (Path(run['scratch_directory']) / 'password.txt').exists()
    assert run['sources_unchanged_during_run']
    commands = {item['name']: item['exit'] for item in run['commands']}
    assert commands['stop'] == 0 and commands['stopped-status'] == 3
    assert commands['actual-wss' if name.startswith('stationary-') else 'actual-mining-outage'] == (1 if name == 'attempt-1' else 0)
    assert run['runtime_sha256'] == (final if fixed else baseline)['runtime_sha256']
    assert run['build_sha256'] == final['build_sha256']
    assert run['efsn_source_sha256'] == (final if fixed else baseline)['efsn_source_sha256']
    source_changes = [key for key, value in run['source_sha256'].items() if sources[key] != value]
    assert source_changes == ([] if fixed else ['test/efsn-mining-outage.test.cjs'])
    runner = ('run-stationary' if name.startswith('stationary-') else 'run') + ('-fixed' if fixed else '') + '.py'
    assert run['runner_sha256'] == digest(bundle / runner)
    assert read(bundle / name / 'proxy/process.json')['result'] == [0, None]
for run in [baseline, final]:
    for name, value in run['runtime_sha256'].items():
        assert digest(root / name) == value, name
previous = read(bundle.parent / 'restart-dashboard-wss-2026-10-03/attempt-4/result.json')
go_changes = [name for name, value in final['efsn_source_sha256'].items() if previous['efsn_source_sha256'][name] != value]
assert go_changes == ['ethstats/ethstats.go', 'tests/restart/dashboard_telemetry_linux_test.go']
assert [name for name, value in baseline['efsn_source_sha256'].items() if final['efsn_source_sha256'][name] != value] == ['ethstats/ethstats.go']
for name, value in final['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
assert record['go_fixture_sha256'] == final['efsn_source_sha256']['tests/restart/dashboard_telemetry_linux_test.go']
assert record['reporter_sha256'] == final['efsn_source_sha256']['ethstats/ethstats.go']
assert final['build_sha256'] == previous['build_sha256']
for name, value in final['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
contracts = read(bundle / 'contracts-1/result.json')
assert [name for name, value in contracts['source_sha256'].items() if sources[name] != value] == ['test/efsn-mining-outage.test.cjs']
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
assert '# pass 173\n# fail 0\n' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 13\n# fail 0\n' in (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
stationary = read(bundle / 'stationary-2/comparison.json')
assert stationary['truth']['mining'] is False and stationary['truth']['head']['number'] == '0x3c'
assert stationary['errors'] == stationary['finalCaptured']['writer']['errors'] == []
assert len(stationary['truth']['history']) == 50
assert [item['name'] for item in stationary['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert stationary['browser']['errors'] == stationary['browser']['foreignRequests'] == []
assert stationary['browser']['security']['protocol'] == 'TLS 1.3'
assert stationary['browser']['certificateSpki'] == read(bundle / 'stationary-2/result.json')['certificate_spki']
assert 'ERR_CERT_AUTHORITY_INVALID' in stationary['browser']['certificateError']
failed = read(bundle / 'attempt-1/result-mining.json')
assert not failed['passed'] and failed['nodeExit'] == [0, None]
assert 'assert.ok(history)' in (bundle / 'attempt-1/actual-mining-outage.stdout.txt').read_text(encoding='utf-8')
data = read(bundle / 'attempt-3/result-mining.json')
assert data['passed'] and data['nodeExit'] == [0, None]
before, stopped, during, after = data['phases']
assert before['label'] == 'before-outage' and stopped['label'] == 'collector-stopped'
assert during['label'] == 'twelve-blocks-without-collector' and after['label'] == 'recovered-with-next-mined-block'
assert during['number'] - stopped['number'] >= 12
assert int(during['nonce'], 16) - int(stopped['nonce'], 16) >= 12
assert after['number'] > during['number'] and int(after['nonce'], 16) > int(during['nonce'], 16)
assert all(phase['mining'] and phase['autoBuy'] and phase['peers'] == '0x0' and phase['tickets'] > 0 for phase in data['phases'])
assert data['initialCollectorPid'] != data['restoredCollectorPid']
assert data['outageStarted'] < data['expired']['time'] < data['restoredAt'] < data['recoveredAt']
assert data['expired']['response']['status'] == 503
assert data['expired']['response']['body'] == {'error': 'snapshot_unavailable'}
assert data['recoveredSnapshot']['response']['status'] == 200
assert data['recoveredSnapshot']['response']['tls']['authorized']
assert data['recoveredSnapshot']['response']['tls']['protocol'] == 'TLSv1.3'
assert len(data['purchases']) == after['number'] - before['number']
parent_hash = before['head']['hash']
nonce = int(before['nonce'], 16)
for item in data['purchases']:
    block, receipt, purchase = item['block'], item['receipt'], item['purchase']
    assert block['parentHash'] == parent_hash
    assert block['miner'] == data['ready']['owner']
    assert len(block['transactions']) == 1
    tx = block['transactions'][0]
    assert int(tx['nonce'], 16) == nonce
    assert tx['from'] == data['ready']['owner']
    assert tx['to'].lower() == '0xffffffffffffffffffffffffffffffffffffffff'
    assert receipt['status'] == '0x1' and receipt['transactionHash'] == tx['hash']
    assert receipt['blockHash'] == block['hash']
    assert purchase.get('Error', '') == '' and purchase['TicketOwner'].lower() == data['ready']['owner']
    assert len(purchase['TicketID']) == 66
    nonce += 1
    parent_hash = block['hash']
assert parent_hash == after['head']['hash'] and nonce == int(after['nonce'], 16)
assert set(data['writer']['errors']) == {'Collector connection closed unexpectedly', 'Collector connection failed'}
assert data['writerErrorsAfterRecovery'] == len(data['writer']['errors'])
captured = read(bundle / 'attempt-3/collector-after.json')
messages = [row['message']['emit'] for row in captured['records'] if row['direction'] == 'incoming' and isinstance(row['message'], dict) and 'emit' in row['message']]
assert len([message for message in messages if message[0] == 'hello']) == 1
history = next(message[1]['history'] for message in messages if message[0] == 'history' and len(message[1]['history']) == 50)
live = [message[1]['block'] for message in messages if message[0] == 'block']
assert live and all(block['number'] >= during['number'] for block in live)
recovered = data['recoveredHistorySnapshot']
assert recovered['response']['status'] == 200 and recovered['response']['tls']['authorized']
heights = recovered['snapshot']['payload']['charts']['height']
assert len(heights) == 40 and heights == list(range(heights[-1] - 39, heights[-1] + 1))
assert heights[-1] >= after['number']
assert recovered['snapshot']['payload']['charts']['transactions'] == [1] * 40
for item in data['purchases']:
    block = item['block']
    number = int(block['number'], 16)
    if stopped['number'] < number <= during['number']:
        report = next(value for value in history + live if value['number'] == number)
        assert report['hash'] == block['hash']
        assert report['parentHash'] == block['parentHash']
        assert [tx['hash'] for tx in report['transactions']] == [tx['hash'] for tx in block['transactions']]
old = read(bundle / 'attempt-2/collector-after.json')['records']
old_heads = [row['message']['emit'][1]['block']['number'] for row in old if row['direction'] == 'incoming' and isinstance(row['message'], dict) and row['message'].get('emit', [None])[0] == 'block']
old_views = [row['message']['emit'][1]['nodes'][0]['stats']['block']['number'] for row in old if row['direction'] == 'outgoing' and isinstance(row['message'], dict) and row['message'].get('emit', [None])[0] == 'init' and row['message']['emit'][1]['nodes']]
assert old_heads[:2] == [73, 62] and 62 in old_views
views = [row['message']['emit'][1]['nodes'][0]['stats']['block']['number'] for row in captured['records'] if row['direction'] == 'outgoing' and isinstance(row['message'], dict) and row['message'].get('emit', [None])[0] == 'init' and row['message']['emit'][1]['nodes']]
assert views and all(number >= during['number'] for number in views)
assert read(bundle / 'linux-process-cleanup.json')['count'] == 0
assert read(bundle / 'windows-process-cleanup.json')['count'] == 0
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'dashboard_application_changes': 0, 'node_reporter_correction': 'P17', 'dashboard_non_markdown_sources': len(sources), 'efsn_changed_sources': go_changes, 'unchanged_efsn_go_and_module_sources': len(previous['efsn_source_sha256']) - 2, 'unchanged_frontend_build_files': len(final['build_sha256']), 'contracts_passed': 173, 'wire_tests_passed': 13, 'stationary_browser_checkpoints': 4, 'outage_mined_blocks': during['number'] - stopped['number'], 'audited_purchases': len(data['purchases']), 'outage_seconds': (data['restoredAt'] - data['outageStarted']) / 1000, 'head_recovery_seconds': (data['recoveredAt'] - data['restoredAt']) / 1000, 'history_blocks': len(history), 'recovered_chart_heights': len(heights), 'baseline_reported_heads': old_heads, 'corrected_reported_heads': [block['number'] for block in live], 'stopped_databases': 5, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
