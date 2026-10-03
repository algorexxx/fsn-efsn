import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
result = json.loads((evidence / 'attempt-2/result.json').read_text(encoding='utf-8'))
first = json.loads((evidence / 'attempt-1/result.json').read_text(encoding='utf-8'))
dashboard = Path(result['dashboard_directory'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


for name, digest in result['source_sha256'].items():
    data = subprocess.check_output(git + ['show', commit['dashboard_commit'] + ':' + name])
    require(hashlib.sha256(data).hexdigest() == digest, f'Tested source differs from commit: {name}')
    if name not in ['wsclient/collect-snapshots.js', 'test/snapshot-collector.test.cjs']:
        require(first['source_sha256'][name] == digest, f'Unexpected change after first run: {name}')
for name in ['wsclient/collect-snapshots.js', 'test/snapshot-collector.test.cjs']:
    data = (evidence / 'attempt-1' / Path(name).name).read_bytes()
    require(hashlib.sha256(data).hexdigest() == first['source_sha256'][name], f'First candidate source differs: {name}')
require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^'], text=True).strip() == commit['base'], 'Wrong ancestry')
patch = (evidence / 'dashboard-snapshots.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash mismatch')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', 'package-lock.json', 'react-frontend/package-lock.json', 'api-server/package-lock.json', 'server.js', 'lib/node.js', 'lib/collection.js', 'lib/history.js']) == b'', 'Unexpected lock or collector change')
clusters = []
for attempt, contracts in [('attempt-1', 98), ('attempt-2', 99)]:
    data = json.loads((evidence / attempt / 'result.json').read_text(encoding='utf-8'))
    require(data['expected_outcome_passed'], f'{attempt} did not pass')
    require(all(item['exit'] == (3 if item['name'] == 'stopped-status' else 0) for item in data['commands']), 'Unexpected command exit')
    require((evidence / attempt / 'psql-control.txt').read_bytes().strip() == b'42', 'Native database check failed')
    for name, count in [('contracts', contracts), ('postgres-tests', 6), ('persistence', 5), ('wire', 1)]:
        text = (evidence / attempt / (name + '.txt')).read_text(encoding='utf-8')
        require(all(line in text.splitlines() for line in [f'# tests {count}', f'# pass {count}', '# fail 0', '# cancelled 0', '# skipped 0']), f'Incomplete {attempt}/{name}')
        require('not ok ' not in text, 'Unexpected test failure')
        require((evidence / attempt / (name + '-stderr.txt')).read_bytes() == b'', 'Unexpected test stderr')
    scratch = Path(data['scratch_directory']).resolve()
    require(scratch.is_relative_to((workspace / 'tmp').resolve()) and scratch.name.startswith('dashboard-postgres-'), 'Unexpected scratch path')
    require(not (scratch / 'password.txt').exists(), 'Generated password file remains')
    status = subprocess.run(['C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe', '-D', str(scratch / 'data'), 'status'], capture_output=True)
    require(status.returncode == 3 and b'no server running' in status.stdout + status.stderr, 'Test cluster still running')
    clusters.append({'directory': str(scratch), 'stopped': True, 'retained_bytes': sum(path.stat().st_size for path in scratch.rglob('*') if path.is_file())})
original = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original checkout status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'Node telemetry source changed')
summary = {
    'evidence_verified': True, 'dashboard_commit': commit['dashboard_commit'],
    'contracts_passed': 99, 'persistence_scenarios_passed': 4, 'persistence_tap_entries': 5,
    'database_scenarios_passed': 5, 'database_tap_entries': 6, 'collector_wire_passed': True,
    'dependency_locks_unchanged': True, 'original_checkout_unchanged': True,
    'test_clusters': clusters, 'public_dashboard_ready': False,
    'remaining': ['Browser stale/error handling and full build', 'Real efsn telemetry and direct RPC comparison', 'Collector resource limits and field validation', 'Production runtime/dependencies, supervision and TLS'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
