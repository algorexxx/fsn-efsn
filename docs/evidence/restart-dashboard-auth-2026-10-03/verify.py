import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
result = json.loads((evidence / 'attempt-1/result.json').read_text(encoding='utf-8'))
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
dashboard = Path(result['dashboard_worktree'])
baseline = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


for name, digest in result['source_sha256'].items():
    require(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest, f'Candidate source changed: {name}')
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
require(subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == commit['dashboard_commit'], 'Wrong dashboard commit')
require(subprocess.check_output(git + ['status', '--porcelain']) == b'', 'Dashboard worktree not clean')
require(subprocess.check_output(git + ['rev-parse', 'HEAD^'], text=True).strip() == commit['base'], 'Unexpected dashboard ancestry')
require(subprocess.check_output(git + ['diff', 'HEAD^', 'HEAD', '--', 'package-lock.json']) == b'', 'Dependency lock changed')
require(hashlib.sha256((evidence / 'dashboard-auth.patch').read_bytes()).hexdigest() == commit['patch_sha256'], 'Review patch changed')
require((evidence / 'dashboard-auth.patch').read_bytes() == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', 'HEAD']), 'Review patch differs from commit')
original = Path(baseline['dashboard_directory'])
for name, digest in baseline['dashboard_source_sha256'].items():
    require(hashlib.sha256((original / name).read_bytes()).hexdigest() == digest, f'Original source changed: {name}')
status = subprocess.check_output(['git', '-C', str(original), '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == baseline['git_status_sha256'], 'Original dashboard status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == baseline['efsn_ethstats_sha256'], 'Node telemetry source changed')
require(result['all_exits_zero'] and all(command['exit'] == 0 for command in result['commands']), 'A retained command failed')
for name in ['syntax-server', 'syntax-credentials']:
    require((evidence / f'attempt-1/{name}.txt').read_bytes() == b'', 'Syntax diagnostics')
for name, count in [('contracts', 71), ('wire', 1)]:
    text = (evidence / f'attempt-1/{name}.txt').read_text(encoding='utf-8')
    require(all(line in text.splitlines() for line in [f'# tests {count}', f'# pass {count}', '# fail 0', '# skipped 0', '# cancelled 0']), 'Incomplete test run')
    require('not ok ' not in text, 'Unexpected failing test')
    require((evidence / f'attempt-1/{name}-stderr.txt').read_bytes() == b'', 'Unexpected test stderr')
require(all((evidence / f'attempt-1/{name}-stderr.txt').read_bytes() == b'' for name in ['syntax-server', 'syntax-credentials']), 'Syntax stderr')
summary = {
    'evidence_verified': True,
    'dashboard_commit': commit['dashboard_commit'],
    'contract_tests_passed': 71,
    'real_loopback_tests_passed': 1,
    'dependency_lock_unchanged': True,
    'original_checkout_unchanged': True,
    'public_dashboard_ready': False,
    'limitations': ['Windows Node 22.11.0 validation; production runtime not selected', 'synthetic wire clients, not a running chain node', 'PostgreSQL/API/browser/TLS/resource-limit acceptance remains open'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
