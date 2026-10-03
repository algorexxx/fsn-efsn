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
previous = read(bundle.parent / 'restart-dashboard-backend-2026-10-03/stationary-1/result.json')
stationary = read(bundle / 'stationary-1/result.json')
proxy = read(bundle / 'proxy-1/result.json')
sources = stationary['source_sha256']
removed = sorted(set(baseline['source_sha256']) - set(sources))
changes = sorted(name for name, value in sources.items() if baseline['source_sha256'].get(name) != value)
assert removed == ['api-server/package-lock.json', 'api-server/package.json']
assert changes == ['package-lock.json', 'package.json']
for name in removed + ['api-server/node_modules']:
    assert not (dashboard / name).exists()
for name, value in sources.items():
    assert digest(dashboard / name) == value, name
for run, runner in [(stationary, 'run-wss.py'), (proxy, 'run-proxy.py')]:
    assert run['passed'] and run['private_removed']
    assert run['source_sha256'] == sources
    assert run['build_sha256'] == previous['build_sha256']
    assert run['runner_sha256'] == digest(bundle / runner)
    for name, value in run['runtime_sha256'].items():
        assert digest(root / name) == value
assert stationary['efsn_source_sha256'] == previous['efsn_source_sha256']
assert all(stationary[name] for name in ['password_removed', 'postgres_pid_absent', 'sources_unchanged_during_run'])
assert not (Path(stationary['scratch_directory']) / 'password.txt').exists()
commands = {row['name']: row['exit'] for row in stationary['commands']}
assert commands['stop'] == 0 and commands['stopped-status'] == 3
assert read(bundle / 'stationary-1/proxy/process.json')['result'] == [0, None]
assert (bundle / 'stationary-1/linux-node-version.stdout.txt').read_text(encoding='utf-8').strip() == 'v24.21.0'
for name, value in previous['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
for name, value in previous['efsn_source_sha256'].items():
    assert digest(root / name) == value
for name, value in proxy['dependency_sha256'].items():
    assert digest(dashboard / name) == value
before = read(bundle / 'inputs/package.json')
before['dependencies']['express'] = '4.22.3'
before['scripts']['start:api'] = 'node api-server/server.js'
assert read(dashboard / 'package.json') == before
lock = read(bundle / 'lock-diff.json')
assert lock['before_entries'] == 156 and lock['after_entries'] == 167
assert len(lock['changes']) == 62
scope = read(bundle / 'lock-scope.json')
assert scope['all_changes_accounted_for'] and scope['changed_paths'] == 62
assert (scope['new_paths'], scope['removed_paths'], scope['updated_paths']) == (18, 7, 37)
for name, value in lock['candidate_sha256'].items():
    assert digest(dashboard / name) == value
install = read(bundle / 'installation.json')
assert install['exit'] == 0 and install['locked_inputs_unchanged'] and install['api_local_dependencies_absent']
assert sorted(install['removed_api_package_files']) == removed
assert '--ignore-scripts' in install['command'] and 'ci' in install['command']
installed = read(bundle / 'installed-packages.json')
assert len(installed) == 167
for item in installed:
    assert digest(dashboard / item['path'] / 'package.json') == item['package_sha256']
    assert read(dashboard / item['path'] / 'package.json')['version'] == item['version']
inspection = read(bundle / 'package-inspection.json')
scratch = root / 'tmp/dashboard-api-packages'
assert inspection['version'] == '4.22.3'
assert digest(scratch / 'express-4.22.3.tgz') == inspection['archive_sha256']
for name, value in inspection['selected_files_sha256'].items():
    assert digest(scratch / name) == value
    assert digest(dashboard / 'node_modules/express' / name) == value
resolution = read(bundle / 'api-resolution.json')
assert resolution['version'] == '4.22.3' and resolution['runtime'] == 'v24.21.0'
assert resolution['rootExpress'] == resolution['apiExpress']
assert resolution['check_sha256'] == digest(bundle / 'check-api-resolution.cjs')
assert resolution['apiStart'] == 'node api-server/server.js'
audit = read(bundle / 'audit-after.json')
old_audit = read(bundle.parent / 'restart-dashboard-backend-2026-10-03/audit-after.json')
cleared = sorted(set(old_audit['vulnerabilities']) - set(audit['vulnerabilities']))
assert cleared == ['body-parser', 'cookie', 'debug', 'express', 'ms', 'path-to-regexp', 'qs', 'send', 'serve-static']
assert not set(audit['vulnerabilities']) - set(old_audit['vulnerabilities'])
assert audit['metadata']['vulnerabilities'] == {'info': 0, 'low': 0, 'moderate': 1, 'high': 6, 'critical': 2, 'total': 9}
assert {row['name'] for row in read(bundle / 'remaining-paths.json')} == set(audit['vulnerabilities'])
contracts = read(bundle / 'contracts-1/result.json')
assert contracts['source_sha256'] == sources
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
for name, count in [('test', 178), ('test-wire', 14)]:
    output = (bundle / 'contracts-1' / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '# pass ' + str(count) + '\n# fail 0\n# cancelled 0\n' in output
web = read(bundle / 'stationary-1/comparison.json')
assert web['errors'] == web['finalCaptured']['writer']['errors'] == []
assert web['truth']['head']['number'] == '0x3c' and web['truth']['mining'] is False
assert len(web['truth']['history']) == 50
assert [row['name'] for row in web['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert web['browser']['errors'] == web['browser']['foreignRequests'] == []
assert web['browser']['security']['protocol'] == 'TLS 1.3'
assert web['browser']['certificateSpki'] == stationary['certificate_spki']
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
    assert record['base'] == baseline['commit']
    assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
    patch = (bundle / 'dashboard-api.patch').read_bytes()
    assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
    assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
    changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
    assert sorted(changed) == sorted(['README.md', 'docs/api-dependency-upgrade.md', 'docs/runtime-dependency-review.md', 'docs/snapshot-storage.md'] + changes + removed)
result = {'verified': True, 'dashboard_commit': commit, 'changed_non_markdown': changes, 'removed_non_markdown': removed, 'application_code_changes': 0, 'unchanged_efsn_sources': len(previous['efsn_source_sha256']), 'unchanged_frontend_build_files': len(previous['build_sha256']), 'contracts': 178, 'socket_tests': 14, 'actual_wss_browser_checkpoints': 4, 'proxy_passed': True, 'single_backend_lock_verified': True, 'cleared_audit_packages': cleared, 'remaining_root_findings': 9, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
if commit:
    (bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
