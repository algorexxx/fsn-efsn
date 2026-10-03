import hashlib
import json
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'baseline.json')
stationary = read(bundle / 'stationary-1/result.json')
previous = read(bundle.parent / 'restart-dashboard-geoip-2026-10-03/stationary-1/result.json')
sources = stationary['source_sha256']
changes = sorted(name for name, value in sources.items() if baseline['source_sha256'].get(name) != value)
removed = sorted(set(baseline['source_sha256']) - set(sources))
assert changes == ['.github/workflows/validate.yml', 'react-frontend/package-lock.json', 'react-frontend/package.json']
assert removed == ['.github/workflows/deploy.yml']
assert not (dashboard / removed[0]).exists()
for name, value in sources.items():
    assert digest(dashboard / name) == value, name
assert stationary['passed'] and stationary['private_removed']
assert stationary['efsn_source_sha256'] == previous['efsn_source_sha256']
for name, value in previous['efsn_source_sha256'].items():
    assert digest(root / name) == value
assert stationary['runner_sha256'] == digest(bundle / 'run-wss.py')
for name, value in stationary['runtime_sha256'].items():
    assert digest(root / name) == value
assert all(stationary[name] for name in ['password_removed', 'postgres_pid_absent', 'sources_unchanged_during_run'])
assert not (Path(stationary['scratch_directory']) / 'password.txt').exists()
commands = {row['name']: row['exit'] for row in stationary['commands']}
assert commands['stop'] == 0 and commands['stopped-status'] == 3
assert read(bundle / 'stationary-1/proxy/process.json')['result'] == [0, None]
assert (bundle / 'stationary-1/linux-node-version.stdout.txt').read_text(encoding='utf-8').strip() == 'v24.21.0'
manifest = read(bundle / 'inputs/package.json')
unused = read(bundle / 'unused-review.json')
assert unused['no_removed_direct_imports_or_compiled_modules']
assert len(unused['removed_direct_dependencies']) == 13
for name in unused['removed_direct_dependencies']:
    del manifest['dependencies'][name]
manifest['dependencies']['axios'] = '0.34.0'
manifest['engines'] = {'node': '>=24.0.0'}
assert read(frontend / 'package.json') == manifest
lock = read(bundle / 'lock-diff.json')
assert (lock['before_entries'], lock['after_entries'], len(lock['changes'])) == (1515, 1445, 75)
scope = read(bundle / 'lock-scope.json')
assert scope['all_changes_accounted_for'] and scope['outside_paths'] == []
assert (scope['new_paths'], scope['removed_paths'], scope['updated_paths']) == (2, 72, 1)
for name, value in lock['candidate_sha256'].items():
    assert digest(frontend / name) == value
installed = read(bundle / 'installed-packages.json')
assert len(installed['installed']) == 1425 and len(installed['omitted_optional']) == 20
assert installed['all_axios_archive_files_match']
for item in installed['installed']:
    assert digest(frontend / item['path'] / 'package.json') == item['package_sha256']
    assert read(frontend / item['path'] / 'package.json')['version'] == item['version']
for item in installed['omitted_optional']:
    assert item['optional'] and not (frontend / item['path']).exists()
for path in installed['removed_paths_absent']:
    assert not (frontend / path).exists()
assert len(installed['removed_paths_absent']) == 72
install = read(bundle / 'installation.json')
assert install['exit'] == 0 and install['locked_inputs_unchanged']
assert all(argument in install['command'] for argument in ['--ignore-scripts', 'ci', 'npm_config_engine_strict=true'])
inspection = read(bundle / 'package-inspection.json')
assert inspection['version'] == '0.34.0'
assert digest(root / 'tmp/axios-0.34.0.tgz') == inspection['archive_sha256']
assert len(inspection['files']) == 78
for name, value in inspection['files'].items():
    assert digest(frontend / 'node_modules/axios' / name) == value['sha256']
provenance = read(bundle / 'provenance.json')
assert provenance['integrity_matches_selected']
assert all(row['exit'] == 0 for row in provenance['commands'])
assert read(bundle / 'provenance-lock.json')['packages']['node_modules/axios']['integrity'] == read(frontend / 'package-lock.json')['dependencies']['axios']['integrity']
signature_output = (bundle / 'provenance-check.stdout.txt').read_text(encoding='utf-8')
assert '23 packages have verified registry signatures' in signature_output and '1 package has a verified attestation' in signature_output
old_audit, audit = read(bundle / 'audit-before.json'), read(bundle / 'audit-after.json')
assert sorted(set(old_audit['vulnerabilities']) - set(audit['vulnerabilities'])) == ['axios', 'd3-color', 'highcharts']
assert not set(audit['vulnerabilities']) - set(old_audit['vulnerabilities'])
assert audit['metadata']['vulnerabilities'] == {'info': 0, 'low': 3, 'moderate': 4, 'high': 66, 'critical': 0, 'total': 73}
assert [name for name, item in audit['vulnerabilities'].items() if item['isDirect']] == ['react-scripts']
toolchain = read(bundle / 'remaining-toolchain-paths.json')
assert toolchain['outside_react_scripts'] == {'acorn': ['node_modules/falafel/node_modules/acorn']}
assert toolchain['outside_owner'] == 'react-datamaps'
contracts = read(bundle / 'contracts-1/result.json')
assert contracts['source_sha256'] == sources
assert contracts['results'] == [{'name': 'test', 'exit': 0}, {'name': 'test:wire', 'exit': 0}]
for name, count in [('test', 178), ('test-wire', 14)]:
    output = (bundle / 'contracts-1' / (name + '.stdout.txt')).read_text(encoding='utf-8')
    assert '# pass ' + str(count) + '\n# fail 0\n# cancelled 0\n' in output
build = read(bundle / 'frontend-1/result.json')
assert all(row['exit'] == 0 for row in build['commands'])
assert [row['name'] for row in build['commands']] == ['react-tests', 'build']
assert 'Tests:       8 passed, 8 total' in (bundle / 'frontend-1/react-tests.stderr.txt').read_text(encoding='utf-8')
assert stationary['build_sha256'] == build['build_sha256']
for name, value in build['build_sha256'].items():
    assert digest(frontend / 'build' / name) == value
activation = read(bundle / 'build-activation.json')
assert activation['hashesVerified'] and activation['oldBuildPreserved']
for name, value in baseline['build_sha256'].items():
    assert digest(Path(activation['retainedBuild']) / name) == value
compiled = read(bundle / 'compiled-review.json')
assert (compiled['old_build_files'], compiled['new_build_files'], compiled['unchanged_build_files']) == (547, 547, 542)
assert compiled['audited_names_in_compiled_sources'] == []
assert compiled['axios_xhr_present'] and compiled['axios_http_absent']
browser = read(bundle / 'browser-result.json')
assert browser['passed'] and browser['errors'] == browser['foreignRequests'] == []
assert [item['name'] for item in browser['results']] == ['populated', 'keyboard-pin', 'map', 'empty', 'storage-failure', 'recovered', 'expired-storage', 'request-timeout', 'timeout-recovery']
assert len(browser['failedRequests']) == 1 and browser['failedRequests'][0]['error'] == 'net::ERR_ABORTED'
assert not any(item['status'] == 404 for item in browser['responses'])
assert read(bundle / 'browser-process.json') == {'passed': True, 'browser_exit': 0, 'server_exit': 0, 'server_stopped': True}
web = read(bundle / 'stationary-1/comparison.json')
assert web['errors'] == web['finalCaptured']['writer']['errors'] == []
assert web['truth']['head']['number'] == '0x3c' and web['truth']['mining'] is False
assert len(web['truth']['history']) == 50
assert [row['name'] for row in web['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert web['browser']['errors'] == web['browser']['foreignRequests'] == []
assert web['browser']['security']['protocol'] == 'TLS 1.3'
assert web['browser']['certificateSpki'] == stationary['certificate_spki']
workflow = read(bundle / 'workflow-review.json')
assert workflow['parsed'] and workflow['deploymentRemoved'] and workflow['hostedRunPerformed'] is False
assert workflow['actions'] == read(bundle / 'actions.json')
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
    patch = (bundle / 'dashboard-frontend.patch').read_bytes()
    assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
    assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
    changed = subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines()
    assert sorted(changed) == sorted(['README.md', 'react-frontend/README.md', 'docs/build-validation.md', 'docs/frontend-dependency-upgrade.md', 'docs/runtime-dependency-review.md'] + changes + removed)
result = {'verified': True, 'dashboard_commit': commit, 'changed_non_markdown': changes, 'removed_non_markdown': removed, 'application_code_changes': 0, 'unchanged_efsn_sources': len(previous['efsn_source_sha256']), 'contracts': 178, 'socket_tests': 14, 'react_dom_tests': 8, 'compiled_browser_checkpoints': 9, 'actual_wss_browser_checkpoints': 4, 'build_files': 547, 'unchanged_build_files': 542, 'installed_frontend_packages': 1425, 'omitted_optional_packages': 20, 'cleared_frontend_audit_packages': ['axios', 'd3-color', 'highcharts'], 'remaining_frontend_findings': 73, 'remaining_audited_names_in_compiled_sources': [], 'backend_manifest_and_lock_unchanged': True, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
if commit:
    (bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
