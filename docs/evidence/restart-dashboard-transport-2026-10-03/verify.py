import hashlib
import json
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


previous = read(bundle.parent / 'restart-dashboard-runtime-review-2026-10-03/inventory.json')
stationary = read(bundle / 'stationary-1/result.json')
mining = read(bundle / 'attempt-1/result.json')
proxy = read(bundle / 'proxy-1/result.json')
sources = stationary['source_sha256']
changes = sorted(name for name, value in sources.items() if previous['source_sha256'][name] != value)
assert changes == ['package-lock.json', 'package.json', 'test/collector-input-wire.test.cjs', 'test/fixtures/wire-server.cjs']
assert set(sources) == set(previous['source_sha256'])
for name, value in sources.items():
    assert digest(dashboard / name) == value, name
for label, run, runner in [('stationary-1', stationary, 'run-wss.py'), ('attempt-1', mining, 'run-mining.py'), ('proxy-1', proxy, 'run-proxy.py')]:
    assert run['passed'] and run['private_removed']
    assert run['source_sha256'] == sources
    assert run['build_sha256'] == previous['build_sha256']
    assert run['runner_sha256'] == digest(bundle / runner)
    for name, value in run['runtime_sha256'].items():
        assert digest(root / name) == value, name
    if label != 'proxy-1':
        assert run['sources_unchanged_during_run'] and run['password_removed'] and run['postgres_pid_absent']
        assert not (Path(run['scratch_directory']) / 'password.txt').exists()
        commands = {row['name']: row['exit'] for row in run['commands']}
        assert commands['stop'] == 0 and commands['stopped-status'] == 3
        assert read(bundle / label / 'proxy/process.json')['result'] == [0, None]
        assert (bundle / label / 'linux-node-version.stdout.txt').read_text(encoding='utf-8').strip() == 'v24.21.0'
for name, value in proxy['dependency_sha256'].items():
    assert digest(dashboard / name) == value
for name, value in previous['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
old_run = read(bundle.parent / 'restart-dashboard-runtime-review-2026-10-03/stationary-1/result.json')
assert stationary['efsn_source_sha256'] == mining['efsn_source_sha256'] == old_run['efsn_source_sha256']
for name, value in stationary['efsn_source_sha256'].items():
    assert digest(root / name) == value
before = read(bundle.parent / 'restart-dashboard-runtime-review-2026-10-03/inputs/package.json')
before['dependencies'].update(primus='8.0.9', ws='8.22.0')
assert read(dashboard / 'package.json') == before
lock_changes = read(bundle / 'lock-diff.json')
assert len(lock_changes['changes']) == 17
for name, value in lock_changes['candidate_sha256'].items():
    assert digest(dashboard / name) == value
install = read(bundle / 'installation.json')
assert install['exit'] == 0 and install['locked_inputs_unchanged']
assert '--ignore-scripts' in install['command'] and 'ci' in install['command']
installed = read(bundle / 'installed-packages.json')
assert len(installed) == 333
for item in installed:
    assert digest(dashboard / item['path'] / 'package.json') == item['package_sha256']
    assert read(dashboard / item['path'] / 'package.json')['version'] == item['version']
for item in read(bundle / 'package-inspection.json'):
    scratch = root / 'tmp/dashboard-transport-packages'
    assert digest(scratch / (item['name'] + '-' + item['version'] + '.tgz')) == item['archive_sha256']
    for name, value in item['selected_files_sha256'].items():
        assert digest(scratch / item['name'] / name) == value
audit = read(bundle / 'audit-after.json')
old_audit = read(bundle.parent / 'restart-dashboard-runtime-review-2026-10-03/backend-audit.json')
assert set(old_audit['vulnerabilities']) - set(audit['vulnerabilities']) == {'ws', 'primus', 'setheader'}
assert not set(audit['vulnerabilities']) - set(old_audit['vulnerabilities'])
assert audit['metadata']['vulnerabilities'] == {'info': 0, 'low': 5, 'moderate': 6, 'high': 18, 'critical': 12, 'total': 41}
contracts = read(bundle / 'contracts-2/result.json')
assert contracts['source_sha256'] == sources
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
for name, count in [('test', 173), ('test-wire', 14)]:
    output = (bundle / 'contracts-2' / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '# pass ' + str(count) + '\n# fail 0\n# cancelled 0\n' in output
first = read(bundle / 'contracts-1/result.json')
assert first['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 1}]
assert sorted(name for name, value in first['source_sha256'].items() if sources[name] != value) == ['test/collector-input-wire.test.cjs', 'test/fixtures/wire-server.cjs']
failed = (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
assert '# pass 12\n# fail 0\n# cancelled 1\n' in failed and 'test timed out after 10000ms' in failed
web = read(bundle / 'stationary-1/comparison.json')
assert web['errors'] == web['finalCaptured']['writer']['errors'] == []
assert web['truth']['head']['number'] == '0x3c' and web['truth']['mining'] is False
assert len(web['truth']['history']) == 50
assert [row['name'] for row in web['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert web['browser']['errors'] == web['browser']['foreignRequests'] == []
assert web['browser']['security']['protocol'] == 'TLS 1.3'
assert web['browser']['certificateSpki'] == stationary['certificate_spki']
data = read(bundle / 'attempt-1/result-mining.json')
assert data['passed'] and data['nodeExit'] == [0, None]
before, stopped, during, after = data['phases']
assert [row['number'] for row in data['phases']] == [61, 61, 73, 74]
assert all(row['mining'] and row['autoBuy'] and row['tickets'] == 2 and row['peers'] == '0x0' for row in data['phases'])
assert int(during['nonce'], 16) - int(stopped['nonce'], 16) == 12
assert data['expired']['response']['status'] == 503 and data['recoveredSnapshot']['response']['status'] == 200
assert data['recoveredSnapshot']['response']['tls']['authorized']
assert len(data['purchases']) == 13
parent = before['head']['hash']
nonce = int(before['nonce'], 16)
for item in data['purchases']:
    block, receipt, purchase = item['block'], item['receipt'], item['purchase']
    assert block['parentHash'] == parent and block['miner'] == data['ready']['owner']
    assert len(block['transactions']) == 1
    transaction = block['transactions'][0]
    assert int(transaction['nonce'], 16) == nonce and transaction['from'] == data['ready']['owner']
    assert transaction['to'].lower() == '0xffffffffffffffffffffffffffffffffffffffff'
    assert receipt['status'] == '0x1' and receipt['transactionHash'] == transaction['hash'] and receipt['blockHash'] == block['hash']
    assert purchase.get('Error', '') == '' and purchase['TicketOwner'].lower() == data['ready']['owner']
    assert len(purchase['TicketID']) == 66
    nonce += 1
    parent = block['hash']
assert parent == after['head']['hash'] and nonce == int(after['nonce'], 16)
assert set(data['writer']['errors']) == {'Collector connection closed unexpectedly', 'Collector connection failed'}
assert data['writerErrorsAfterRecovery'] == len(data['writer']['errors']) == 538
capture = read(bundle / 'attempt-1/collector-after.json')
messages = [row['message']['emit'] for row in capture['records'] if row['direction'] == 'incoming' and isinstance(row['message'], dict) and 'emit' in row['message']]
heads = [row[1]['block']['number'] for row in messages if row[0] == 'block']
assert heads == [73, 73, 74, 74]
assert any(row[0] == 'history' and len(row[1]['history']) == 50 for row in messages)
charts = data['recoveredHistorySnapshot']['snapshot']['payload']['charts']
assert charts['height'] == list(range(35, 75)) and charts['transactions'] == [1] * 40
proxy_data = read(bundle / 'proxy-1/proxy.json')
assert proxy_data['checks'] == dict.fromkeys(['certificateTrustAndHostname', 'compiledAssets', 'routeIsolation', 'staleSnapshotUnavailable', 'reporterConnectionLimit', 'authentication', 'complete'], True)
assert proxy_data['errors'] == [] and len(proxy_data['forwardedHeaders']) == 8
assert proxy_data['historyBytes'] == 3276956 and proxy_data['heartbeatCount'] == 24
assert all(row['headers']['x-forwarded-for'] == '127.0.0.1' for row in proxy_data['forwardedHeaders'])
for name in ['active', 'idle']:
    assert read(bundle / 'proxy-1' / name / 'process.json')['result'] == [0, None]
for name in ['linux', 'windows']:
    assert read(bundle / (name + '-process-cleanup.json'))['count'] == 0
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
commit = None
if '--precommit' not in sys.argv:
    record = read(bundle / 'commit.json')
    commit = record['dashboard_commit']
    assert record['base'] == '539a0df782fbe123c5704e48708c5751bfe94cd3'
    assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
    patch = (bundle / 'dashboard-transport.patch').read_bytes()
    assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
    assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
    changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
    assert sorted(changed) == ['docs/collector-input-limits.md', 'docs/runtime-dependency-review.md', 'docs/transport-upgrade.md'] + changes
result = {'verified': True, 'dashboard_commit': commit, 'changed_non_markdown': changes, 'application_code_changes': 0, 'unchanged_efsn_sources': len(stationary['efsn_source_sha256']), 'unchanged_frontend_build_files': len(previous['build_sha256']), 'contracts': 173, 'socket_tests': 14, 'actual_wss_browser_checkpoints': 4, 'proxy_passed': True, 'mining_outage_blocks': 12, 'audited_ticket_purchases': 13, 'outage_seconds': (data['restoredAt'] - data['outageStarted']) / 1000, 'recovery_seconds': (data['recoveredAt'] - data['restoredAt']) / 1000, 'cleared_audit_packages': ['primus', 'setheader', 'ws'], 'remaining_root_findings': 41, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
if commit:
    (bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
