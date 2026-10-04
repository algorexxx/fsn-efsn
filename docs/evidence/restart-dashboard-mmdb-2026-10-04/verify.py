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


def flatten(dependencies, prefix=''):
    result = {}
    for name, item in dependencies.items():
        key = prefix + name
        result[key] = {field: value for field, value in item.items() if field != 'dependencies'}
        result.update(flatten(item.get('dependencies', {}), key + '/node_modules/'))
    return result


baseline = read(bundle / 'baseline.json')
native = read(bundle / 'stationary-2/result.json')
assert native['passed'] and native['sources_unchanged_during_run']
for name, value in native['source_sha256'].items():
    assert digest(dashboard / name) == value, name
for name, value in native['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
assert len(native['efsn_source_sha256']) == 1007
for run in ['stationary-1', 'stationary-2']:
    result = read(bundle / run / 'result.json')
    assert all(result[key] for key in ['password_removed', 'private_removed', 'postgres_pid_absent'])
assert read(bundle / 'stationary-1/result.json')['passed'] is False
assert 'Unexpected end of JSON input' in (bundle / 'stationary-1/actual-wss.stdout.txt').read_text(encoding='utf-8')
assert all(result['exit'] == 0 for result in read(bundle / 'contracts-3/result.json'))
assert 'pass 204' in (bundle / 'contracts-3/contracts.stdout.txt').read_text(encoding='utf-8')
assert 'pass 14' in (bundle / 'contracts-2/wire.stdout.txt').read_text(encoding='utf-8')
assert 'expected: /GEOIP_MODE/' in (bundle / 'contracts-2/contracts.stdout.txt').read_text(encoding='utf-8')
assert 'node: not found' in (bundle / 'contracts-1/contracts.stderr.txt').read_text(encoding='utf-8')
assert '23 passed, 23 total' in (bundle / 'frontend-1/react-tests.stderr.txt').read_text(encoding='utf-8')
assert all(item['exit'] == 0 for item in read(bundle / 'frontend-2/result.json')['commands'])
assert (bundle / 'frontend-2/build.stderr.txt').read_bytes() == b''
build = read(bundle / 'frontend-2/result.json')['build_sha256']
for name, value in build.items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
assert build == native['build_sha256']
previous_build = read(bundle.parent / 'restart-dashboard-pins-2026-10-04/frontend-1/result.json')['build_sha256']
for name, value in previous_build.items():
    assert digest(root / 'tmp/dashboard-mmdb-build-before' / name) == value
assert read(bundle / 'build-comparison.json')['executable_assets_unchanged']
browser = read(bundle / 'browser-result.json')
assert browser['passed'] and len(browser['results']) == 12 and browser['errors'] == browser['foreignRequests'] == []
assert read(bundle / 'browser-process.json')['server_stopped']
checkpoints = read(bundle / 'stationary-2/browser-checkpoints.json')
assert len(checkpoints['checkpoints']) == 4 and checkpoints['errors'] == checkpoints['foreignRequests'] == []
audit = read(bundle / 'install-1/audit.stdout.txt')
assert audit['metadata']['vulnerabilities']['total'] == 0
assert all(item['exit'] == 0 for item in read(bundle / 'install-1/result.json'))
old = json.loads(subprocess.check_output(['git', '-C', str(dashboard), 'show', baseline['dashboard_commit'] + ':package-lock.json']))
new = read(dashboard / 'package-lock.json')
old_entries = flatten(old['dependencies'])
new_entries = flatten(new['dependencies'])
removed = sorted(old_entries.keys() - new_entries.keys())
added = sorted(new_entries.keys() - old_entries.keys())
assert len(removed) == 11 and added == ['mmdb-lib']
assert all(old_entries[name] == new_entries[name] for name in old_entries.keys() & new_entries.keys())
reader_metadata = read(bundle.parent / 'restart-dashboard-geoip-reader-2026-10-04/mmdb-lib-metadata.json')
assert new_entries['mmdb-lib']['integrity'] == reader_metadata['dist']['integrity']
fixture_manifest = read(bundle.parent / 'restart-dashboard-geoip-reader-2026-10-04/fixtures.json')
for local, original in [('city.mmdb', 'test-data/GeoLite2-City-Test.mmdb'), ('not-city.mmdb', 'test-data/MaxMind-DB-test-ipv6-24.mmdb'), ('LICENSE-MIT', 'LICENSE-MIT')]:
    assert digest(dashboard / 'test/fixtures/geoip' / local) == fixture_manifest[original]['sha256']
previous_data = read(bundle.parent / 'restart-dashboard-geoip-validation-2026-10-04/validation-1/result.json')['data_sha256']['bundled']
for name, value in previous_data.items():
    assert digest(root / 'tmp/dashboard-mmdb-backend-before/geoip-lite/data' / name) == value
assert not (dashboard / 'node_modules/geoip-lite').exists()
retired = ['lib/geoip-dataset.js', 'test/geoip-dataset.test.cjs', 'test/fixtures/geoip-data.json']
assert all(not (dashboard / name).exists() for name in retired)
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
for path in bundle.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
processes = subprocess.check_output(['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'ps', '-eo', 'pid=,args=']).decode()
remaining = [line for line in processes.splitlines() if '/tmp/fsn-stats-auth/test/fixtures/' in line or '/tmp/dashboard-mining-fixed-tests' in line]
assert remaining == [], remaining
result = {'verified': True, 'backend_contracts': 204, 'socket_tests': 14, 'frontend_tests': 23, 'compiled_browser_checkpoints': 12, 'native_browser_checkpoints': 4, 'backend_audit_advisories': 0, 'removed_dependency_entries': removed, 'added_dependency_entries': added, 'other_lock_entries_unchanged': True, 'final_build_files': len(build), 'old_build_and_dataset_preserved': True, 'original_dashboard_preserved': True, 'unchanged_efsn_sources': len(native['efsn_source_sha256']), 'retired_paths_absent': retired, 'remaining_linux_fixture_processes': 0, 'source_sha256': native['source_sha256'], 'public_deployment_performed': False}
if (bundle / 'commit.json').exists():
    commit = read(bundle / 'commit.json')
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'status', '--porcelain']) == b''
    assert digest(bundle / 'dashboard-mmdb.patch') == commit['patch_sha256']
    subprocess.run(['git', '-C', str(dashboard), 'apply', '--reverse', '--check', str(bundle / 'dashboard-mmdb.patch')], check=True)
    result.update(dashboard_commit=commit['dashboard_commit'], portable_patch_reverse_check=True)
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'source_sha256'}, indent=2))
