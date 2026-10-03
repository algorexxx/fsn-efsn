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


inventory = read(bundle / 'inventory.json')
audit = read(bundle / 'audit-capture.json')
assert audit['dashboard_commit'] == 'd70014342f1995807bccd26370a7b86379c89099'
assert audit['inputs_unchanged']
for name, value in audit['inputs'].items():
    assert digest(bundle / 'inputs' / name) == value
    assert digest(dashboard / name) == value
for item in audit['commands']:
    assert item['exit'] == 1 and item['error'] is None
    assert item['metadata'] == read(bundle / (item['name'] + '-audit.json'))['metadata']
assert {key: value['audit_counts']['total'] for key, value in inventory['locks'].items()} == {'backend': 44, 'frontend': 76, 'legacy-api': 7}
assert len(inventory['browser']['mapped_packages']) == 41
assert inventory['browser']['audited_packages_in_maps'] == ['axios']
assert any('/adapters/xhr.js' in name for name in inventory['browser']['mapped_packages']['axios'])
assert not any('/adapters/http.js' in name for name in inventory['browser']['mapped_packages']['axios'])
for name, value in inventory['source_sha256'].items():
    assert digest(dashboard / name) == value, name
for name, value in inventory['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
for item in read(bundle / 'metadata/sources.json'):
    assert digest(bundle / 'metadata' / item['file']) == item['sha256']
resolved = read(bundle / 'resolved-packages.json')
assert resolved['node'] == 'v24.21.0'
versions = {(row['entry'], row['name']): row['version'] for row in resolved['entries']}
assert versions[('node_modules/primus/transformers/websockets/server.js', 'ws')] == '1.1.5'
assert versions[('server.js', 'primus')] == '6.1.0'
assert versions[('api-server/app.js', 'express')] == '4.17.1'
assert versions[('db/index.js', 'pg')] == '8.23.1'
assert not (dashboard / 'api-server/node_modules').exists()
for item in read(bundle / 'platform-capture.json')['commands']:
    assert item['exit'] == 0
    suffix = '.json' if item['name'] == 'resolved-packages' else '.txt'
    assert digest(bundle / (item['name'] + suffix)) == item['sha256']
download = read(bundle / 'node-download.json')
assert digest(Path(download['archive'])) == download['archive_sha256']
assert digest(Path(download['binary'])) == download['binary_sha256']
assert download['archive_sha256'] + '  node-v24.21.0-linux-x64.tar.xz' in (bundle / 'node-shasums.txt').read_text(encoding='utf-8')
assert not download['system_installation']
contracts = read(bundle / 'node24-contracts/result.json')
assert contracts == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
for name, count in [('test', 173), ('test-wire', 13)]:
    output = (bundle / 'node24-contracts' / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert 'pass ' + str(count) + '\n' in output and 'fail 0\n' in output
run = read(bundle / 'stationary-1/result.json')
assert run['passed'] and run['password_removed'] and run['private_removed'] and run['postgres_pid_absent']
assert not (Path(run['scratch_directory']) / 'password.txt').exists()
assert run['sources_unchanged_during_run']
assert run['source_sha256'] == inventory['source_sha256']
assert run['build_sha256'] == inventory['build_sha256']
assert run['runner_sha256'] == digest(bundle / 'run-wss.py')
assert (bundle / 'stationary-1/linux-node-version.stdout.txt').read_text(encoding='utf-8').strip() == 'v24.21.0'
commands = {row['name']: row['exit'] for row in run['commands']}
assert commands['actual-wss'] == 0 and commands['stop'] == 0 and commands['stopped-status'] == 3
for name, value in run['runtime_sha256'].items():
    assert digest(root / name) == value, name
previous = read(bundle.parent / 'restart-dashboard-mining-outage-2026-10-03/attempt-3/result.json')
assert run['efsn_source_sha256'] == previous['efsn_source_sha256']
for name, value in run['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
comparison = read(bundle / 'stationary-1/comparison.json')
assert comparison['truth']['mining'] is False and comparison['truth']['head']['number'] == '0x3c'
assert comparison['errors'] == comparison['finalCaptured']['writer']['errors'] == []
assert len(comparison['truth']['history']) == 50
assert [row['name'] for row in comparison['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert comparison['browser']['errors'] == comparison['browser']['foreignRequests'] == []
assert comparison['browser']['security']['protocol'] == 'TLS 1.3'
assert comparison['browser']['certificateSpki'] == run['certificate_spki']
assert 'ERR_CERT_AUTHORITY_INVALID' in comparison['browser']['certificateError']
assert read(bundle / 'stationary-1/proxy/process.json')['result'] == [0, None]
build = read(bundle / 'node24-build/result.json')
assert build['exit'] == 0 and 'CI=true' in build['command']
assert 'Compiled successfully.' in (bundle / 'node24-build/stdout.txt').read_text(encoding='utf-8')
assert set(build['file_sha256']) == set(inventory['build_sha256'])
different = [name for name, value in build['file_sha256'].items() if inventory['build_sha256'][name] != value]
assert different == ['static/js/main.b0947b3d.js.map']
for name, value in build['file_sha256'].items():
    assert digest(Path(build['output']) / name) == value, name
linux = read(bundle / 'linux-process-cleanup.json')
assert linux['count'] == 0 and linux['postgres_pid_absent'] and linux['private_removed']
assert read(bundle / 'windows-process-cleanup.json')['count'] == 0
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
record = read(bundle / 'commit.json')
assert record['base'] == audit['dashboard_commit']
assert subprocess.check_output(git + ['rev-parse', record['dashboard_commit'] + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-runtime.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', record['dashboard_commit']])
changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', record['dashboard_commit']]).decode().splitlines()
assert sorted(changed) == ['docs/build-validation.md', 'docs/deployment-configuration.md', 'docs/runtime-dependency-review.md']
result = {
    'verified': True,
    'dashboard_commit': record['dashboard_commit'],
    'application_or_dependency_changes': 0,
    'unchanged_dashboard_non_markdown_files': len(inventory['source_sha256']),
    'unchanged_efsn_go_and_module_sources': len(run['efsn_source_sha256']),
    'unchanged_original_build_files': len(inventory['build_sha256']),
    'node24_contracts': 173,
    'node24_socket_tests': 13,
    'node24_actual_wss_browser_checkpoints': 4,
    'node24_production_build': True,
    'build_difference': different,
    'audit_package_findings': {key: value['audit_counts'] for key, value in inventory['locks'].items()},
    'stopped_databases': 1,
    'remaining_test_processes': 0,
    'original_dashboard_preserved': True,
    'public_deployment_approved': False,
}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
