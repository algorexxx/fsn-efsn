import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
result = json.loads((evidence / 'attempt-2/result.json').read_text(encoding='utf-8'))
first = json.loads((evidence / 'attempt-1/result.json').read_text(encoding='utf-8'))
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
baseline = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
dashboard = Path(result['dashboard_worktree'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


for name, digest in result['source_sha256'].items():
    source = subprocess.check_output(git + ['show', commit['dashboard_commit'] + ':' + name])
    require(hashlib.sha256(source).hexdigest() == digest, f'Tested source differs from commit: {name}')
    if name != 'test/deployment-wiring.test.cjs':
        require(first['source_sha256'][name] == digest, f'Unexpected source change after first attempt: {name}')
require(hashlib.sha256((evidence / 'attempt-1/deployment-wiring.test.cjs').read_bytes()).hexdigest() == first['source_sha256']['test/deployment-wiring.test.cjs'], 'First test harness changed')
require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^'], text=True).strip() == commit['base'] == result['dashboard_base'], 'Unexpected ancestry')
require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', 'package-lock.json', 'react-frontend/package-lock.json', 'api-server/package-lock.json']) == b'', 'Dependency locks changed')
patch = (evidence / 'dashboard-config.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash changed')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
review = json.loads((evidence / 'inherited-source-review.json').read_text(encoding='utf-8'))
require(review['reviewed_at_commit'] == commit['dashboard_commit'], 'Wrong source review commit')
for name, digest in review['source_sha256'].items():
    source = subprocess.check_output(git + ['show', commit['dashboard_commit'] + ':' + name])
    require(hashlib.sha256(source).hexdigest() == digest, f'Wrong inherited source: {name}')
    require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', name]) == b'', f'Unexpected persistence change: {name}')
original = Path(baseline['dashboard_directory'])
for name, digest in baseline['dashboard_source_sha256'].items():
    require(hashlib.sha256((original / name).read_bytes()).hexdigest() == digest, f'Original checkout source changed: {name}')
status = subprocess.check_output(['git', '-C', str(original), '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == baseline['git_status_sha256'], 'Original checkout status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == baseline['efsn_ethstats_sha256'], 'Node telemetry source changed')
require(result['all_exits_zero'] and all(item['exit'] == 0 for item in result['commands']), 'Final commands did not pass')
require(not first['all_exits_zero'], 'First attempt failure missing')
for attempt, count, passed, failed in [('attempt-1', 86, 84, 2), ('attempt-2', 86, 86, 0)]:
    text = (evidence / attempt / 'contracts.txt').read_text(encoding='utf-8')
    require(all(line in text.splitlines() for line in [f'# tests {count}', f'# pass {passed}', f'# fail {failed}', '# skipped 0', '# cancelled 0']), 'Incomplete contract results')
    wire = (evidence / attempt / 'wire.txt').read_text(encoding='utf-8')
    require(all(line in wire.splitlines() for line in ['# tests 1', '# pass 1', '# fail 0', '# skipped 0', '# cancelled 0']), 'Incomplete wire results')
    for index in range(1, 7):
        require((evidence / attempt / f'syntax-{index}.txt').read_bytes() == b'', 'Syntax diagnostics')
    require(all(path.read_bytes() == b'' for path in (evidence / attempt).glob('*-stderr.txt')), 'Unexpected stderr')
summary = {
    'evidence_verified': True,
    'dashboard_commit': commit['dashboard_commit'],
    'contract_tests_passed': 86,
    'real_collector_wire_tests_passed': 1,
    'real_http_api_with_stubbed_storage_in_contracts': True,
    'first_attempt_harness_failures_retained': 2,
    'dependency_locks_unchanged': True,
    'original_checkout_unchanged': True,
    'public_dashboard_ready': False,
    'limitations': ['Windows Node 22.11.0; production runtime not selected', 'No PostgreSQL or full browser build', 'Persistence and schema blockers remain', 'No public proxy/TLS deployment or resource-limit acceptance'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
