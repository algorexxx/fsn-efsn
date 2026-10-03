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


baseline = read(bundle / 'baseline.json')
previous = read(bundle.parent / 'restart-dashboard-transport-2026-10-03/stationary-1/result.json')
stationary = read(bundle / 'stationary-1/result.json')
mining = read(bundle / 'attempt-1/result.json')
sources = stationary['source_sha256']
removed = sorted(set(baseline['source_sha256']) - set(sources))
changes = sorted(name for name, value in sources.items() if baseline['source_sha256'].get(name) != value)
assert removed == ['lib/express.js']
assert changes == ['lib/collection.js', 'lib/history.js', 'package-lock.json', 'package.json', 'server.js', 'test/history.test.cjs']
assert not (dashboard / 'lib/express.js').exists()
for name, value in sources.items():
    assert digest(dashboard / name) == value, name
for label, run, runner in [('stationary-1', stationary, 'run-wss.py'), ('attempt-1', mining, 'run-mining.py')]:
    assert all(run[key] for key in ['passed', 'private_removed', 'password_removed', 'postgres_pid_absent', 'sources_unchanged_during_run'])
    assert run['source_sha256'] == sources
    assert run['build_sha256'] == previous['build_sha256']
    assert run['efsn_source_sha256'] == previous['efsn_source_sha256']
    assert run['runner_sha256'] == digest(bundle / runner)
    for name, value in run['runtime_sha256'].items():
        assert digest(root / name) == value, name
    assert not (Path(run['scratch_directory']) / 'password.txt').exists()
    commands = {row['name']: row['exit'] for row in run['commands']}
    assert commands['stop'] == 0 and commands['stopped-status'] == 3
    assert read(bundle / label / 'proxy/process.json')['result'] == [0, None]
    assert (bundle / label / 'linux-node-version.stdout.txt').read_text(encoding='utf-8').strip() == 'v24.21.0'
for name, value in previous['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
for name, value in previous['efsn_source_sha256'].items():
    assert digest(root / name) == value
dependencies_removed = ['auto-bind', 'body-parser', 'debug', 'grunt', 'grunt-contrib-clean', 'grunt-contrib-concat', 'grunt-contrib-copy', 'grunt-contrib-cssmin', 'grunt-contrib-jade', 'grunt-contrib-uglify', 'http2', 'jade']
before = read(bundle / 'inputs/package.json')
for name in dependencies_removed:
    del before['dependencies'][name]
before['dependencies']['lodash'] = '4.18.1'
assert read(dashboard / 'package.json') == before
lock = read(bundle / 'lock-diff.json')
assert lock['before_entries'] == 333 and lock['after_entries'] == 156
assert len([row for row in lock['changes'] if row['after'] is None]) == 177
updates = [row for row in lock['changes'] if row['after'] is not None]
assert len(updates) == 1 and updates[0]['path'] == 'node_modules/lodash'
for name, value in lock['candidate_sha256'].items():
    assert digest(dashboard / name) == value
install = read(bundle / 'installation.json')
assert install['exit'] == 0 and install['locked_inputs_unchanged']
assert '--ignore-scripts' in install['command'] and 'ci' in install['command']
installed = read(bundle / 'installed-packages.json')
assert len(installed) == 156
for item in installed:
    assert digest(dashboard / item['path'] / 'package.json') == item['package_sha256']
    assert read(dashboard / item['path'] / 'package.json')['version'] == item['version']
for name in ['auto-bind', 'grunt', 'grunt-contrib-clean', 'grunt-contrib-concat', 'grunt-contrib-copy', 'grunt-contrib-cssmin', 'grunt-contrib-jade', 'grunt-contrib-uglify', 'http2', 'jade']:
    assert not (dashboard / 'node_modules' / name).exists(), name
inspection = read(bundle / 'package-inspection.json')
scratch = root / 'tmp/dashboard-backend-packages'
assert digest(scratch / 'lodash-4.18.1.tgz') == inspection['archive_sha256']
for name, value in inspection['selected_files_sha256'].items():
    assert digest(scratch / name) == value
    assert digest(dashboard / 'node_modules/lodash' / name) == value
audit = read(bundle / 'audit-after.json')
old_audit = read(bundle.parent / 'restart-dashboard-transport-2026-10-03/audit-after.json')
cleared = sorted(set(old_audit['vulnerabilities']) - set(audit['vulnerabilities']))
assert len(cleared) == 23 and 'lodash' in cleared
assert not set(audit['vulnerabilities']) - set(old_audit['vulnerabilities'])
assert audit['metadata']['vulnerabilities'] == {'info': 0, 'low': 3, 'moderate': 2, 'high': 11, 'critical': 2, 'total': 18}
baseline_test = read(bundle / 'baseline-test.json')
assert baseline_test['exit'] == 0 and baseline_test['lodash'] == '3.10.1'
assert baseline_test['test_sha256'] == digest(dashboard / 'test/history.test.cjs')
contracts = read(bundle / 'contracts-2/result.json')
assert contracts['source_sha256'] == sources
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
for name, count in [('test', 178), ('test-wire', 14)]:
    output = (bundle / 'contracts-2' / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '# pass ' + str(count) + '\n# fail 0\n# cancelled 0\n' in output
failed = read(bundle / 'contracts-1/result.json')
assert sorted(name for name, value in failed['source_sha256'].items() if sources[name] != value) == ['lib/history.js']
assert 'thru is not a function' in (bundle / 'contracts-1/test.stdout.txt').read_text(encoding='utf-8')
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
assert before['number'] == stopped['number'] == 61
assert during['number'] - stopped['number'] >= 10 and after['number'] > during['number']
assert all(row['mining'] and row['autoBuy'] and row['tickets'] == 2 and row['peers'] == '0x0' for row in data['phases'])
assert int(during['nonce'], 16) - int(stopped['nonce'], 16) == during['number'] - stopped['number']
assert data['expired']['response']['status'] == 503 and data['recoveredSnapshot']['response']['status'] == 200
assert data['recoveredSnapshot']['response']['tls']['authorized']
assert len(data['purchases']) == after['number'] - before['number']
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
assert data['writerErrorsAfterRecovery'] == len(data['writer']['errors'])
charts = data['recoveredHistorySnapshot']['snapshot']['payload']['charts']
assert charts['height'] == list(range(after['number'] - 39, after['number'] + 1)) and charts['transactions'] == [1] * 40
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
    assert record['base'] == baseline['commit']
    assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
    patch = (bundle / 'dashboard-backend.patch').read_bytes()
    assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
    assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
    changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
    assert sorted(changed) == sorted(['README.md', 'docs/backend-cleanup.md', 'docs/runtime-dependency-review.md'] + changes + removed)
result = {'verified': True, 'dashboard_commit': commit, 'changed_non_markdown': changes, 'removed_non_markdown': removed, 'unchanged_efsn_sources': len(previous['efsn_source_sha256']), 'unchanged_frontend_build_files': len(previous['build_sha256']), 'contracts': 178, 'socket_tests': 14, 'actual_wss_browser_checkpoints': 4, 'mining_outage_blocks': during['number'] - stopped['number'], 'audited_ticket_purchases': len(data['purchases']), 'outage_seconds': (data['restoredAt'] - data['outageStarted']) / 1000, 'recovery_seconds': (data['recoveredAt'] - data['restoredAt']) / 1000, 'cleared_audit_packages': cleared, 'remaining_root_findings': 18, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
if commit:
    (bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
