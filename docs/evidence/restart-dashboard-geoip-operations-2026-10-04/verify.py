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
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = read(bundle / 'source-baseline.json')
for name, value in baseline['dashboard_sha256'].items():
    if not name.endswith('.md'):
        assert digest(dashboard / name) == value, name
for name, value in baseline['efsn_sha256'].items():
    assert digest(root / name) == value, name
run = bundle / 'run-3'
assert read(run / 'summary.json')['passed']
for name, value in read(run / 'baseline.json')['package_sha256'].items():
    assert digest(dashboard / 'node_modules/geoip-lite' / name) == value, name
records = read(run / 'results.json')
assert [r['mode'] for r in records] == ['missing-license', 'checksum-503', 'empty-checksum', 'corrupt-zip', 'city-503', 'stall-city', 'checksum-mismatch', 'unchanged-missing', 'success', 'retry-success']
assert all(r['active_unchanged'] and r['process_stopped'] for r in records)
checks = {
    'missing-license': ('stdout', 'Missing license_key'),
    'checksum-503': ('stdout', 'HTTP Request Failed [503 Service Unavailable]'),
    'empty-checksum': ('stdout', 'Could not retrieve checksum'),
    'corrupt-zip': ('stderr', 'End of central directory record signature not found'),
    'city-503': ('stdout', 'HTTP Request Failed [503 Service Unavailable]'),
    'checksum-mismatch': ('stdout', 'Successfully Updated Databases from MaxMind.'),
    'unchanged-missing': ('stdout', 'Database "city" is up to date'),
    'success': ('stdout', 'Successfully Updated Databases from MaxMind.'),
    'retry-success': ('stdout', 'Successfully Updated Databases from MaxMind.'),
}
for mode, (stream, marker) in checks.items():
    assert marker in (run / (mode + '.' + stream + '.txt')).read_text(encoding='utf-8'), mode
assert records[5]['killed_after_deadline'] and records[5]['exit'] == -9
expected = read(run / 'fixture-inputs.json')['expected_sha256']
assert records[8]['after'] == records[9]['after'] == expected
assert records[6]['exit'] == 0 and records[6]['after']['country.checksum'] == hashlib.sha256(b'0' * 64).hexdigest()
assert records[7]['exit'] == 0 and records[7]['before'] == records[7]['after'] and records[7]['lookup']['exit'] != 0
switch = read(bundle / 'switch-1/result.json')
assert read(bundle / 'switch-1/summary.json')['passed']
assert all(switch[key] for key in ['reader_stopped', 'datasets_unchanged']) and switch['final_target'] == 'active-a'
for key, country, city, coordinates in [
    ('initial', 'SE', 'Fixture A', [59.3293, 18.0686]),
    ('after_rejected_candidate', 'SE', 'Fixture A', [59.3293, 18.0686]),
    ('running_after_switch', 'SE', 'Fixture A', [59.3293, 18.0686]),
    ('fresh_after_switch', 'NO', 'Fixture B', [59.9139, 10.7522]),
    ('fresh_after_rollback', 'SE', 'Fixture A', [59.3293, 18.0686]),
]:
    assert [None if n['geo'] is None else [n['geo']['country'], n['geo']['city'], n['geo']['ll']] for n in switch[key]['nodes']] == [[country, city, coordinates]] * 3 + [None]
assert switch['incomplete_lookup']['exit'] == 0
assert switch['incomplete_lookup']['value']['map'] == [{'name': 'fixture-1', 'radius': 2, 'latitude': 0, 'longitude': 0, 'fillKey': 'bubbleFill'}]
processes = subprocess.check_output(['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'ps', '-eo', 'pid=,args=']).decode()
matching = [line.strip() for line in processes.splitlines() if 'geoip-operations-2026-10-04/lookup.cjs' in line or 'geoip-lite/scripts/updatedb.js' in line]
assert matching == [], matching
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
summary = {'verified': True, 'offline_updater_cases': 10, 'lookup_switch_checkpoints': 5, 'incomplete_dataset_characterized': True, 'remaining_fixture_processes': 0, 'dependency_package_unchanged': True, 'dashboard_non_markdown_unchanged': True, 'efsn_sources_unchanged': len(baseline['efsn_sha256']), 'original_dashboard_preserved': True, 'live_download_tested': False, 'hosted_service_restart_tested': False, 'public_deployment_approved': False}
if (bundle / 'commit.json').is_file():
    commit = read(bundle / 'commit.json')
    assert commit['base'] == baseline['dashboard_commit']
    assert digest(bundle / 'dashboard-geoip-operations.patch') == commit['patch_sha256']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    summary['dashboard_commit'] = commit['dashboard_commit']
(bundle / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
