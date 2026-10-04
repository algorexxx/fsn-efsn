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
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


baseline = read(bundle / 'baseline.json')
result = read(bundle / 'run-3/result.json')
expected_checkpoints = ['late-collector-start', 'collector-crash-recovery', 'writer-crash-recovery', 'api-crash-recovery', 'database-recovery', 'pending-write-shutdown', 'stale-and-recover', 'intentional-stop', 'restart-limit', 'configuration-repair', 'credential-log-check', 'journal-rotation']
assert result['passed']
assert [item['name'] for item in result['checkpoints']] == expected_checkpoints
for name, value in result['source_sha256'].items():
    assert digest(dashboard / name) == value, name
for name, value in baseline['dashboard_source_sha256'].items():
    if name != 'docs/snapshot-storage.md':
        assert digest(dashboard / name) == value, name
for name, value in baseline['efsn_source_sha256'].items():
    assert digest(root / name) == value, name
for name, value in baseline['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value, name
for label in ['run-1', 'run-2', 'run-3']:
    run = read(bundle / label / 'result.json')
    assert run['cleanup'] == {'errors': [], 'unit_files_removed': True, 'postgres_pid_absent': True, 'fixture_processes_stopped': True, 'private_plaintext_removed': True}
    assert all(state['MainPID'] == '0' and state['ControlGroup'] == '' for state in run['final_states'].values())
    for name, value in run['runner_sha256'].items():
        assert digest(bundle / label / name) == value, (label, name)
assert read(bundle / 'run-1/result.json')['passed'] is False
assert read(bundle / 'run-2/result.json')['passed'] is False
assert 'ECONNREFUSED' in (bundle / 'run-1/reporter.log').read_text(encoding='utf-8')
assert 'not loaded' in read(bundle / 'run-2/result.json')['failure']
assert (bundle / 'run-3/unit-verify.stderr.txt').read_bytes() == b''
assert 'Runtime Journal' in (bundle / 'run-3/application-journal.stdout.txt').read_text(encoding='utf-8')
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value, name
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
previous_runtimes = read(bundle.parent / 'restart-dashboard-mmdb-2026-10-04/stationary-2/result.json')['runtime_sha256']
for name, value in previous_runtimes.items():
    assert digest(root / name) == value, name
for path in bundle.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
record = {'verified': True, 'checkpoints': expected_checkpoints, 'unchanged_efsn_sources': len(baseline['efsn_source_sha256']), 'unchanged_compiled_build_files': len(baseline['build_sha256']), 'prior_dashboard_application_and_dependencies_preserved': True, 'original_dashboard_preserved': True, 'previous_runtime_binaries_preserved': True, 'public_deployment_performed': False, 'source_sha256': result['source_sha256']}
if (bundle / 'commit.json').exists():
    commit = read(bundle / 'commit.json')
    assert subprocess.check_output(['git', '-C', str(dashboard), 'rev-parse', 'HEAD']).decode().strip() == commit['dashboard_commit']
    assert subprocess.check_output(['git', '-C', str(dashboard), 'status', '--porcelain']) == b''
    assert digest(bundle / 'dashboard-supervision.patch') == commit['patch_sha256']
    subprocess.run(['git', '-C', str(dashboard), 'apply', '--reverse', '--check', str(bundle / 'dashboard-supervision.patch')], check=True)
    record.update(dashboard_commit=commit['dashboard_commit'], portable_patch_reverse_check=True)
(bundle / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
