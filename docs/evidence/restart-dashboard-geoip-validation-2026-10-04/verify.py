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


baseline = read(bundle / 'source-baseline.json')
contracts = read(bundle / 'contracts-2/result.json')
unit = read(bundle / 'unit.json')
expected_changes = ['deploy/validate-geoip.cjs', 'lib/geoip-dataset.js', 'package.json', 'test/collector-output-wire.test.cjs', 'test/fixtures/geoip-data.json', 'test/geoip-dataset.test.cjs']
changed = sorted(name for name, value in contracts['source_sha256'].items() if baseline['dashboard_sha256'].get(name) != value)
assert changed == expected_changes
for name, value in contracts['source_sha256'].items():
    assert digest(dashboard / name) == unit['source_sha256'].get(name, value), name
assert all(row['exit'] == 0 for row in contracts['results']) and unit['exit'] == 0
assert '# tests 237\n' in (bundle / 'contracts-2/test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 14\n' in (bundle / 'contracts-2/test-wire.stdout.txt').read_text(encoding='utf-8')
assert '# pass 59\n' in (bundle / 'unit.stdout.txt').read_text(encoding='utf-8')
initial = (bundle / 'contracts-1/test-wire.stdout.txt').read_text(encoding='utf-8')
assert '4925 !== 8077' in initial and '# fail 1\n' in initial
for name, value in baseline['efsn_sha256'].items():
    assert digest(root / name) == value, name
previous_package = json.loads(subprocess.check_output(['git', '-C', str(dashboard), 'show', baseline['dashboard_commit'] + ':package.json']))
current_package = read(dashboard / 'package.json')
expected_package = dict(previous_package)
expected_package['scripts'] = dict(previous_package['scripts'])
expected_package['scripts']['test'] += ' test/geoip-dataset.test.cjs'
assert current_package == expected_package
assert digest(dashboard / 'package-lock.json') == baseline['dashboard_sha256']['package-lock.json']
package_baseline = read(bundle.parent / 'restart-dashboard-geoip-operations-2026-10-04/run-3/baseline.json')
for name, value in package_baseline['package_sha256'].items():
    assert digest(dashboard / 'node_modules/geoip-lite' / name) == value, name
build = read(bundle.parent / 'restart-dashboard-pins-2026-10-04/frontend-1/result.json')['build_sha256']
for name, value in build.items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
validation = read(bundle / 'validation-1/result.json')
assert all(validation[key] for key in ['passed', 'valid_fixture_accepted', 'narrow_ipv6_rejected', 'bundled_dataset_rejected', 'all_data_unchanged'])
assert validation['reader_expected_countries_from_encoded_records'] == ['NO', 'SE']
assert validation['reader_observed_countries'] == ['NO', 'NO']
scratch = root / 'tmp/dashboard-geoip-validation-1'
for label, directory in [('valid', scratch / 'valid'), ('precision', scratch / 'precision'), ('bundled', dashboard / 'node_modules/geoip-lite/data')]:
    for name, value in validation['data_sha256'][label].items():
        assert digest(directory / name) == value, name
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
processes = subprocess.check_output(['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'ps', '-eo', 'pid=,args=']).decode()
matching = [line.strip() for line in processes.splitlines() if '/tmp/fsn-stats-auth/test/fixtures/' in line or 'geoip-validation-2026-10-04/probe-reader.cjs' in line or '/tmp/fsn-stats-auth/deploy/validate-geoip.cjs' in line]
assert matching == [], matching
result = {'verified': True, 'changed_non_markdown': changed, 'backend_contracts': 237, 'new_validator_tests': 59, 'socket_tests': 14, 'initial_socket_failure_retained': True, 'valid_fixture_accepted': True, 'bundled_dataset_rejected': True, 'ipv6_precision_mismatch_reproduced': True, 'dependencies_and_lock_unchanged': True, 'unchanged_build_files': len(build), 'unchanged_efsn_sources': len(baseline['efsn_sha256']), 'original_dashboard_preserved': True, 'remaining_linux_fixture_processes': 0, 'public_deployment_approved': False}
if (bundle / 'commit.json').is_file():
    commit = read(bundle / 'commit.json')
    assert commit['base'] == baseline['dashboard_commit']
    assert digest(bundle / 'dashboard-geoip-validation.patch') == commit['patch_sha256']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    result['dashboard_commit'] = commit['dashboard_commit']
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
