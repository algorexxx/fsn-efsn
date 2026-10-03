import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
capture = json.loads((evidence / 'capture.json').read_text(encoding='utf-8'))
dashboard = Path(capture['dashboard_directory'])


def require(condition, message):
    if not condition:
        raise ValueError(message)


for name, digest in capture['dashboard_source_sha256'].items():
    require(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest, f'Dashboard source changed: {name}')
require(hashlib.sha256((evidence / 'baseline/server.js').read_bytes()).hexdigest() == capture['dashboard_source_sha256']['server.js'], 'Archived collector mismatch')
require(hashlib.sha256((evidence / 'collector-contract.test.cjs').read_bytes()).hexdigest() == capture['harness_sha256'], 'Harness changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == capture['efsn_ethstats_sha256'], 'Node telemetry source changed')
require(all(value['after_crlf_normalization'] for value in capture['inspected_sources_vs_head'].values()), 'Inspected source differs from recorded HEAD beyond line endings')
git = ['git', '-C', str(dashboard), '-c', 'core.safecrlf=false', '-c', 'core.autocrlf=false']
require(subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == capture['dashboard_head'], 'Dashboard HEAD changed')
status = subprocess.check_output(git + ['status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == capture['git_status_sha256'], 'Dashboard Git status changed')
for folder, code in [('baseline', '7'), ('attempt-2', '1')]:
    root = evidence / folder
    require((root / 'exit.txt').read_text(encoding='utf-8').strip() == code, 'Missing failed launch exit')
    require((root / 'tests.tap').read_bytes() == b'', 'Failed launch unexpectedly ran tests')
    require('EPERM' in (root / 'stderr.txt').read_text(encoding='utf-8'), 'Missing launch error')
root = evidence / 'attempt-3'
require((root / 'exit.txt').read_text(encoding='utf-8').strip() == '1', 'Expected baseline contract failure')
require((root / 'stderr.txt').read_bytes() == b'', 'Unexpected contract-run stderr')
tap = (root / 'tests.tap').read_text(encoding='utf-8')
results = re.findall(r'^(not )?ok (\d+) - (.+)$', tap, re.MULTILINE)
expected = [
    ('', '1', 'ordinary hello and same-node stats reach the collector'),
    ('not ', '2', 'missing telemetry secret prevents listening'),
    ('not ', '3', 'empty telemetry secret prevents listening'),
    ('not ', '4', 'stats require a successful hello on the same session'),
    ('not ', '5', 'stats identity remains bound to the authenticated session'),
    ('not ', '6', 'rejected hello does not disclose its secret to logging'),
    ('', '7', 'disconnect marks the originating session inactive'),
]
require(results == expected, 'Baseline behavior or test identities differ')
require(all(line in tap.splitlines() for line in ['# tests 7', '# pass 2', '# fail 5', '# cancelled 0', '# skipped 0', '# todo 0']), 'Incomplete run')
summary = {
    'evidence_verified': True,
    'dashboard_acceptance_passed': False,
    'passed_contracts': 2,
    'failed_contracts': 5,
    'skipped_contracts': 0,
    'source_and_status_unchanged': True,
    'scope': capture['scope'],
    'limitations': ['handler contract tests with doubles, not real network or database integration', 'dependency/build/browser readiness not established', 'no production source fixes included'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
