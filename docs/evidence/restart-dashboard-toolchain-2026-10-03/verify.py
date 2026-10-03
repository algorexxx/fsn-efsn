import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
frontend = dashboard / 'react-frontend'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'baseline.json')
old_lock = read(bundle / 'inputs/package-lock.json')
lock = read(frontend / 'package-lock.json')
manifest = read(frontend / 'package.json')
assert lock['lockfileVersion'] == 3
assert not any(p.endswith('/react-scripts') for p in lock['packages'])
for name in manifest['dependencies']:
    assert lock['packages']['node_modules/' + name]['version'] == old_lock['dependencies'][name]['version'], name
assert lock['packages']['']['devDependencies'] == manifest['devDependencies']
assert not manifest.get('overrides')
installed, omitted = [], []
for path, entry in lock['packages'].items():
    if not path:
        continue
    package = frontend / path / 'package.json'
    if not package.exists():
        assert entry.get('optional'), path
        omitted.append(path)
        continue
    assert read(package)['version'] == entry['version'], path
    installed.append({'path': path, 'version': entry['version'], 'sha256': digest(package)})
audit = read(bundle / 'lint-gap-audit.stdout.txt')
assert audit['metadata']['vulnerabilities']['total'] == 0
assert all(item['exit'] == 0 for item in read(bundle / 'lint-gap-install.json'))
build = read(bundle / 'frontend-5/result.json')
assert all(item['exit'] == 0 for item in build['commands'])
assert not (bundle / 'frontend-5/build.stderr.txt').read_text(encoding='utf-8').strip()
assert 'Tests:       8 passed, 8 total' in (bundle / 'frontend-5/react-tests.stderr.txt').read_text(encoding='utf-8')
assert build['build_sha256'] == read(bundle / 'frontend-4/result.json')['build_sha256']
for path, expected in build['build_sha256'].items():
    assert digest(frontend / 'build' / path) == expected, path
retained = Path(read(bundle / 'build-activation.json')['retainedBuild'])
for path, expected in baseline['build_sha256'].items():
    assert digest(retained / path) == expected, path
browser = read(bundle / 'browser-result.json')
assert browser['passed'] and browser['errors'] == browser['foreignRequests'] == []
assert len(browser['results']) == 9
assert len(browser['failedRequests']) == 1 and browser['failedRequests'][0]['error'] == 'net::ERR_ABORTED'
assert not any(item['status'] == 404 for item in browser['responses'])
assert read(bundle / 'browser-process.json')['server_stopped']
stationary = read(bundle / 'stationary-1/result.json')
assert all(stationary[k] for k in ['passed', 'password_removed', 'private_removed', 'postgres_pid_absent', 'sources_unchanged_during_run'])
assert stationary['build_sha256'] == build['build_sha256']
for name, expected in stationary['source_sha256'].items():
    if name not in ['react-frontend/package.json', 'react-frontend/package-lock.json']:
        assert digest(dashboard / name) == expected, name
native = read(bundle / 'stationary-1/comparison.json')
assert native['errors'] == native['finalCaptured']['writer']['errors'] == []
assert native['truth']['head']['number'] == '0x3c' and len(native['truth']['history']) == 50
assert [r['name'] for r in native['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert native['browser']['errors'] == native['browser']['foreignRequests'] == []
assert native['browser']['security']['protocol'] == 'TLS 1.3'
previous = read(bundle.parent / 'restart-dashboard-frontend-2026-10-03/stationary-1/result.json')
assert stationary['efsn_source_sha256'] == previous['efsn_source_sha256']
for name, expected in previous['efsn_source_sha256'].items():
    assert digest(root / name) == expected, name
for name, expected in baseline['source_sha256'].items():
    if not name.startswith('react-frontend/') and not name.endswith('.md'):
        assert digest(dashboard / name) == expected, name
for name, count in [('test', 178), ('test-wire', 14)]:
    assert '# pass ' + str(count) + '\n# fail 0\n# cancelled 0\n' in (bundle / 'contracts-1' / (name + '.stdout.txt')).read_text(encoding='utf-8')
gates = read(bundle / 'gate-checks.json')
assert len(gates) == 9 and all(row['exit'] == row['expected_exit'] for row in gates)
assert next(row for row in gates if row['name'] == 'undefined.jsx')['tool_exits'] == [0, 1]
compiled = read(bundle / 'compiled-review.json')
assert compiled['axios_xhr_present'] and compiled['axios_http_absent']
assert not any('/src/js/' in name for p in (frontend / 'build').rglob('*.map') for name in read(p).get('sources', []))
for path in (frontend / 'src').rglob('*.js'):
    assert not re.search(r'^import type |/\* @flow \*/', path.read_text(encoding='utf-8'), re.M)
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, expected in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == expected, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
for platform in ['linux', 'windows']:
    assert read(bundle / (platform + '-process-cleanup.json'))['count'] == 0
record = {
    'verified': True, 'lock_paths': len(lock['packages']) - 1, 'installed': len(installed), 'omitted_optional': len(omitted),
    'frontend_advisories': 0, 'backend_manifest_lock_and_code_preserved': True, 'unchanged_efsn_sources': len(previous['efsn_source_sha256']),
    'active_direct_library_versions_preserved': True, 'react_dom_tests': 8, 'backend_contracts': 178, 'socket_tests': 14,
    'browser_checkpoints': 9, 'native_browser_checkpoints': 4, 'build_and_lint_gate_checks': 9, 'build_files': len(build['build_sha256']),
    'accepted_build_identical_after_lint_only_addition': True, 'original_dashboard_preserved': True, 'retained_previous_build': str(retained),
    'remaining_test_processes': 0, 'public_deployment_approved': False,
    'acorn_versions': {p: v['version'] for p, v in lock['packages'].items() if p.endswith('/acorn')},
    'final_manifest_sha256': digest(frontend / 'package.json'), 'final_lock_sha256': digest(frontend / 'package-lock.json'),
}
if '--commit' in sys.argv:
    commit = read(bundle / 'commit.json')
    assert commit['base'] == baseline['commit']
    assert digest(bundle / 'dashboard-toolchain.patch') == commit['patch_sha256']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    record['dashboard_commit'] = commit['dashboard_commit']
(bundle / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
(bundle / 'installed-final.json').write_text(json.dumps({'installed': installed, 'omitted_optional': omitted}, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
