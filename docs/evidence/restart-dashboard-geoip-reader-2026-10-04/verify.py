import base64
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
scratch = root / 'tmp/dashboard-geoip-reader'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


baseline = read(bundle / 'source-baseline.json')
for name, value in baseline['dashboard_sha256'].items():
    assert digest(dashboard / name) == value, name
for name, value in baseline['efsn_sha256'].items():
    assert digest(root / name) == value, name
assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == baseline['dashboard_commit']
assert subprocess.check_output(['git', '-C', str(dashboard), 'status', '--porcelain', '-z']) == b''
build = read(bundle.parent / 'restart-dashboard-pins-2026-10-04/frontend-1/result.json')['build_sha256']
for name, value in build.items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
previous = read(bundle.parent / 'restart-dashboard-geoip-validation-2026-10-04/validation-1/result.json')
for label, directory in [('valid', root / 'tmp/dashboard-geoip-validation-1/valid'), ('precision', root / 'tmp/dashboard-geoip-validation-1/precision'), ('bundled', dashboard / 'node_modules/geoip-lite/data')]:
    for name, value in previous['data_sha256'][label].items():
        assert digest(directory / name) == value, name
for name, hashes in read(bundle / 'legacy-patch.json').items():
    assert digest(dashboard / 'node_modules/geoip-lite/lib' / name) == hashes['original_sha256']
    assert digest(scratch / 'patched-legacy' / name) == hashes['candidate_sha256']
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
fixtures = read(bundle / 'fixtures.json')
for name, value in fixtures.items():
    assert digest(scratch / 'upstream' / name) == value['sha256']
assert digest(scratch / 'expected.json') == read(bundle / 'expectations.json')['expected_sha256']
metadata = read(bundle / 'mmdb-lib-metadata.json')
archive = scratch / 'mmdb-lib-3.0.3.tgz'
assert 'sha512-' + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode() == metadata['dist']['integrity']
package_hashes = {}
with tarfile.open(archive, 'r:gz') as package:
    for member in package.getmembers():
        if member.isfile():
            name = Path(member.name).relative_to('package').as_posix()
            expected = hashlib.sha256(package.extractfile(member).read()).hexdigest()
            assert digest(scratch / 'candidate/node_modules/mmdb-lib' / name) == expected
            package_hashes[name] = expected
assert not metadata.get('dependencies')
assert read(bundle / 'advisories.json')['response'] == {}
assert read(bundle / 'run-1/result.json')['exit'] == 0
summary = read(bundle / 'run-1/stdout.txt')
assert summary == {'passed': True, 'raw_lookup_cases': 3007, 'mapped_lookup_cases': 7, 'mapping_cases': 8}
assert (bundle / 'run-1/stderr.txt').read_bytes() == b''
results = read(bundle / 'reader-results.json')
assert results['runtime'] == 'v24.21.0'
assert all(not item['failures'] for item in results['results'])
for result in read(bundle / 'comparison-1/result.json'):
    assert result['exit'] == 0
    assert (bundle / 'comparison-1' / (result['name'] + '.stderr.txt')).read_bytes() == b''
assert read(bundle / 'comparison-1/legacy-patched.stdout.txt')['actual'] == [None, 'NO', 'SE', None, 'SE']
processes = subprocess.check_output(['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', 'ps', '-eo', 'pid=,args=']).decode()
matching = [line for line in processes.splitlines() if 'geoip-reader-2026-10-04/' in line and any(script in line for script in ['compare.cjs', 'legacy.cjs', 'model.cjs'])]
assert not matching, matching
result = {'verified': True, 'dashboard_commit': baseline['dashboard_commit'], 'unchanged_dashboard_files': len(baseline['dashboard_sha256']), 'unchanged_efsn_sources': len(baseline['efsn_sha256']), 'unchanged_frontend_build_files': len(build), 'original_dashboard_preserved': True, 'previous_geoip_datasets_preserved': True, 'raw_lookup_cases': 3007, 'mapped_lookup_cases': 7, 'mapping_cases': 8, 'node_model_cases': 5, 'legacy_cases_per_reader': 5, 'remaining_comparison_processes': 0, 'downloaded_fixture_bytes': sum(value['bytes'] for value in fixtures.values()), 'package_sha256': package_hashes, 'harness_sha256': {path.name: digest(path) for path in bundle.iterdir() if path.suffix in ['.py', '.cjs']}, 'production_migration_performed': False}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if not key.endswith('sha256')}, indent=2))
