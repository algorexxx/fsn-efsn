import ast
import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


baseline = read(bundle / 'baseline.json')
lifecycle = read(bundle / 'run-1/result.json')
proxy = read(bundle / 'proxy-3/result.json')
native = read(bundle / 'stationary-1/result.json')
expected = ['supervised-https-wss', 'timer-rotation-reopen', 'archive-retention', 'certificate-reload', 'invalid-certificate-refusal', 'worker-crash', 'master-crash', 'intentional-stop']
assert lifecycle['passed'] and [item['name'] for item in lifecycle['checkpoints']] == expected
assert lifecycle['cleanup']['all_paths_removed'] and lifecycle['cleanup']['runtime_units_removed']
assert lifecycle['cleanup']['remaining_processes'] == [] and lifecycle['cleanup']['no_synthetic_secret_in_evidence']
assert lifecycle['final_proxy']['MainPID'] == '0' and lifecycle['final_proxy']['ControlGroup'] == ''
for name, value in lifecycle['source_sha256'].items():
    assert digest(dashboard / name) == value, name
assert proxy['passed'] and proxy['private_removed']
assert read(bundle / 'proxy-3/proxy.json')['checks']['complete']
assert native['passed'] and native['sources_unchanged_during_run']
assert all(native[key] for key in ['password_removed', 'private_removed', 'postgres_pid_absent'])
checkpoints = read(bundle / 'stationary-1/browser-checkpoints.json')
assert len(checkpoints['checkpoints']) == 4 and checkpoints['errors'] == checkpoints['foreignRequests'] == []
for result in [proxy, native]:
    for name, value in result['source_sha256'].items():
        assert digest(dashboard / name) == value, name
    assert result['build_sha256'] == baseline['build_sha256']
    for name, value in result['runtime_sha256'].items():
        assert digest(root / name) == value, name
allowed_changes = ['deploy/nginx.conf.template', 'test/fixtures/nginx.cjs', 'test/proxy-tls.test.cjs', 'docs/service-supervision.md', 'docs/proxy-tls.md']
changed = []
for name, value in baseline['dashboard_source_sha256'].items():
    if digest(dashboard / name) != value:
        changed.append(name)
assert sorted(changed) == sorted(allowed_changes)
for name, value in baseline['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
for name, value in baseline['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
for attempt in ['proxy-1', 'proxy-2']:
    result = read(bundle / attempt / 'result.json')
    assert result['passed'] is False and result['private_removed']
    assert 'asset-manifest.json' in (bundle / attempt / 'proxy-test.stdout.txt').read_text(encoding='utf-8')
    assert result['source_sha256']['test/proxy-tls.test.cjs'] == baseline['dashboard_source_sha256']['test/proxy-tls.test.cjs']
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
cleanup = read(bundle / 'cleanup.json')
assert cleanup['native_database_directory_removed'] and cleanup['remaining_fixture_processes'] == []
for path in bundle.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
record = {'verified': True, 'lifecycle_checkpoints': expected, 'proxy_regression_passed': True, 'native_wss_database_browser_passed': True, 'browser_checkpoints': 4, 'unchanged_efsn_sources': len(baseline['efsn_source_sha256']), 'unchanged_build_files': len(baseline['build_sha256']), 'changed_prior_dashboard_paths': sorted(changed), 'original_dashboard_preserved': True, 'fixtures_cleaned': True, 'public_deployment_performed': False}
if (bundle / 'commit.json').exists():
    commit = read(bundle / 'commit.json')
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'status', '--porcelain']) == b''
    assert digest(bundle / 'dashboard-proxy-lifecycle.patch') == commit['patch_sha256']
    subprocess.run(['git', '-C', str(dashboard), 'apply', '--reverse', '--check', str(bundle / 'dashboard-proxy-lifecycle.patch')], check=True)
    record.update(dashboard_commit=commit['dashboard_commit'], portable_patch_reverse_check=True)
(bundle / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
