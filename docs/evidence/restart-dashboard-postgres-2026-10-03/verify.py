import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
candidate = json.loads((evidence / 'attempt-3/result.json').read_text(encoding='utf-8'))
dashboard = Path(candidate['dashboard_directory'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^'], text=True).strip() == commit['base'], 'Wrong ancestry')
patch = (evidence / 'dashboard-postgres.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash mismatch')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
for attempt, revision in [('attempt-2', commit['base']), ('attempt-3', commit['dashboard_commit'])]:
    result = read_json(evidence / attempt / 'result.json')
    require(result['expected_outcome_passed'], 'Expected database result did not pass')
    for name, digest in result['source_sha256'].items():
        data = subprocess.check_output(git + ['show', revision + ':' + name])
        require(hashlib.sha256(data).hexdigest() == digest, f'Tested source differs: {attempt}/{name}')
    require((evidence / attempt / 'psql-control.txt').read_bytes().strip() == b'42', 'Native connection control failed')
    exits = {item['name']: item['exit'] for item in result['commands']}
    require(exits['initdb'] == exits['start'] == exits['psql-control'] == exits['stop'] == 0 and exits['stopped-status'] == 3, 'Cluster lifecycle failed')
    require(exits['driver-probe'] == (1 if attempt == 'attempt-2' else 0), 'Unexpected driver result')
baseline_probe = read_json(evidence / 'attempt-2/driver-probe.txt')
candidate_probe = read_json(evidence / 'attempt-3/driver-probe.txt')
require(baseline_probe == {'node': 'v22.11.0', 'pg': '7.12.1', 'connected': False, 'error': 'timeout expired'}, 'Unexpected legacy probe')
require(candidate_probe == {'node': 'v22.11.0', 'pg': '8.23.1', 'connected': True, 'rows': [{'value': 42}]}, 'Unexpected corrected probe')
require(read_json(evidence / 'socket-observation.json') == {'node': 'v22.11.0', 'unconnectedSocketState': 'open'}, 'Wrong socket observation')
for name, count in [('contracts', 86), ('postgres-tests', 6), ('wire', 1)]:
    text = (evidence / 'attempt-3' / (name + '.txt')).read_text(encoding='utf-8')
    require(all(line in text.splitlines() for line in [f'# tests {count}', f'# pass {count}', '# fail 0', '# skipped 0', '# cancelled 0']), f'Incomplete {name}')
    require('not ok ' not in text, 'Unexpected failing test')
old = json.loads(subprocess.check_output(git + ['show', commit['base'] + ':package-lock.json']))['dependencies']
new = json.loads(subprocess.check_output(git + ['show', commit['dashboard_commit'] + ':package-lock.json']))['dependencies']
changes = [{'package': name, 'before': old.get(name, {}).get('version'), 'after': new.get(name, {}).get('version')} for name in sorted(set(old) | set(new)) if old.get(name) != new.get(name)]
require(changes == read_json(evidence / 'dependency-changes.json'), 'Dependency change inventory differs')
allowed = {'buffer-writer', 'packet-reader', 'pg', 'pg-cloudflare', 'pg-connection-string', 'pg-pool', 'pg-protocol', 'pgpass', 'postgres-bytea', 'postgres-date', 'split', 'split2', 'through'}
require({item['package'] for item in changes} == allowed, 'Unrelated dependency changes')
metadata = read_json(evidence / 'pg-registry-metadata.json')
require(new['pg']['version'] == metadata['version'] == '8.23.1', 'Wrong pinned driver')
require(new['pg']['integrity'] == metadata['dist.integrity'] and new['pg']['resolved'] == metadata['dist.tarball'], 'Registry integrity mismatch')
require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', 'react-frontend/package-lock.json', 'api-server/package-lock.json']) == b'', 'Other lockfiles changed')
original = read_json(evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original dashboard changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original dashboard status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'Node telemetry source changed')
clusters = []
for attempt in ['attempt-1', 'attempt-2', 'attempt-3']:
    result = read_json(evidence / attempt / 'result.json')
    scratch = Path(result['scratch_directory']).resolve()
    require(scratch.is_relative_to((workspace / 'tmp').resolve()) and scratch.name.startswith('dashboard-postgres-'), 'Unexpected test cluster path')
    require(not (scratch / 'password.txt').exists(), 'Generated password file remains')
    status = subprocess.run(['C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe', '-D', str(scratch / 'data'), 'status'], capture_output=True)
    require(status.returncode == 3 and b'no server running' in status.stdout + status.stderr, 'Test cluster still running')
    clusters.append({'directory': str(scratch), 'stopped': True, 'bytes_retained': sum(path.stat().st_size for path in scratch.rglob('*') if path.is_file())})
summary = {
    'evidence_verified': True, 'dashboard_commit': commit['dashboard_commit'],
    'legacy_failure_reproduced': True, 'replacement_driver_passed': True,
    'contracts_passed': 86, 'database_scenarios_passed': 5, 'database_tap_entries_passed': 6,
    'collector_wire_passed': True, 'original_checkout_unchanged': True,
    'test_clusters': clusters, 'public_dashboard_ready': False,
    'next': 'Persistence protocol, atomic snapshot storage and nondestructive schema; actual pipeline still untested',
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
