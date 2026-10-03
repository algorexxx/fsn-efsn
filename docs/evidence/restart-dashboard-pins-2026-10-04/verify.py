import hashlib
import json
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
stationary = read(bundle / 'stationary-1/result.json')
expected_changes = ['react-frontend/src/Components/Main.js', 'react-frontend/src/pinned-nodes.js', 'react-frontend/src/pinned-nodes.test.js']
changed = sorted(name for name, value in stationary['source_sha256'].items() if baseline['source_sha256'].get(name) != value)
assert changed == expected_changes
for name, value in stationary['source_sha256'].items():
    assert digest(dashboard / name) == value, name
assert all(stationary[k] for k in ['passed', 'password_removed', 'private_removed', 'postgres_pid_absent', 'sources_unchanged_during_run'])
previous = read(bundle.parent / 'restart-dashboard-toolchain-2026-10-03/stationary-1/result.json')
assert stationary['efsn_source_sha256'] == previous['efsn_source_sha256']
for name, value in previous['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
for name, value in baseline['source_sha256'].items():
    if not name.endswith('.md') and name != expected_changes[0]:
        assert digest(dashboard / name) == value, name
build = read(bundle / 'frontend-1/result.json')
assert all(item['exit'] == 0 for item in build['commands'])
assert 'Tests:       22 passed, 22 total' in (bundle / 'frontend-1/react-tests.stderr.txt').read_text(encoding='utf-8')
assert 'Found 0 warnings and 0 errors.' in (bundle / 'frontend-1/build.stdout.txt').read_text(encoding='utf-8')
assert stationary['build_sha256'] == build['build_sha256']
for name, value in build['build_sha256'].items():
    assert digest(frontend / 'build' / name) == value, name
unchanged_build = sum(build['build_sha256'].get(name) == value for name, value in baseline['build_sha256'].items())
sources = [source for path in (frontend / 'build').rglob('*.map') for source in read(path).get('sources', [])]
assert any('/src/pinned-nodes.js' in name for name in sources)
assert not any('/src/pinned-nodes.test.js' in name for name in sources)
retained = Path(read(bundle / 'build-activation.json')['retainedBuild'])
for name, value in baseline['build_sha256'].items():
    assert digest(retained / name) == value, name
before = read(bundle / 'pins-baseline-2/result.json')
after = read(bundle / 'pins-final/result.json')
assert before['passed'] and all(item['rows'] == 0 for item in before['results'])
assert after['passed'] and len(after['results']) == 7
assert all(item['rows'] == 2 and item['errors'] == item['foreign'] == [] for item in after['results'])
for name in ['pins-baseline', 'pins-baseline-2', 'pins-final']:
    assert read(bundle / name / 'process.json')['server_stopped']
browser = read(bundle / 'browser-result.json')
assert browser['passed'] and len(browser['results']) == 9
assert browser['errors'] == browser['foreignRequests'] == []
server = json.loads((bundle / 'browser.stdout.txt').read_text(encoding='utf-8').splitlines()[-1])
assert server['counts']['hanging'] > 0
assert len(browser['failedRequests']) == server['counts']['hanging']
assert all(item == {'url': browser['url'] + '/stats-api/nodes', 'error': 'net::ERR_ABORTED'} for item in browser['failedRequests'])
assert not any(item['status'] == 404 for item in browser['responses'])
assert read(bundle / 'browser-process.json')['server_stopped']
native = read(bundle / 'stationary-1/comparison.json')
assert native['errors'] == native['finalCaptured']['writer']['errors'] == []
assert native['truth']['head']['number'] == '0x3c' and len(native['truth']['history']) == 50
assert [r['name'] for r in native['browser']['checkpoints']] == ['actual-head', 'pinned-actual-head', 'stopped-writer-expired', 'writer-recovered']
assert native['browser']['errors'] == native['browser']['foreignRequests'] == []
assert native['browser']['security']['protocol'] == 'TLS 1.3'
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
for platform in ['linux', 'windows']:
    assert read(bundle / (platform + '-process-cleanup.json'))['count'] == 0
result = {
    'verified': True, 'changed_non_markdown': changed, 'manifest_lock_backend_unchanged': True,
    'unchanged_efsn_sources': len(previous['efsn_source_sha256']), 'react_dom_tests': 8, 'storage_contract_tests': 14,
    'reproduced_baseline_failures': 3, 'storage_browser_scenarios': 7, 'browser_checkpoints': 9, 'native_browser_checkpoints': 4,
    'build_files': len(build['build_sha256']), 'unchanged_build_files': unchanged_build,
    'intentional_hanging_requests': server['counts']['hanging'], 'matching_aborted_api_requests': len(browser['failedRequests']),
    'original_dashboard_preserved': True, 'previous_build_preserved': True, 'remaining_test_processes': 0,
    'public_deployment_approved': False,
}
if '--commit' in sys.argv:
    commit = read(bundle / 'commit.json')
    assert commit['base'] == baseline['commit']
    assert digest(bundle / 'dashboard-pins.patch') == commit['patch_sha256']
    result['dashboard_commit'] = commit['dashboard_commit']
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
