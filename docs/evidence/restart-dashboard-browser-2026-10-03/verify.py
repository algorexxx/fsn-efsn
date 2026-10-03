import hashlib
import json
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
result = json.loads((evidence / 'result.json').read_text(encoding='utf-8'))
dashboard = Path(result['dashboard_directory'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


require(result['base'] == commit['base'], 'Wrong tested parent')
require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^'], text=True).strip() == commit['base'], 'Wrong ancestry')
for name, digest in result['source_sha256'].items():
    data = subprocess.check_output(git + ['show', commit['dashboard_commit'] + ':' + name])
    require(hashlib.sha256(data).hexdigest() == digest, f'Tested source differs: {name}')
patch = (evidence / 'dashboard-browser.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', 'package-lock.json', 'react-frontend/package-lock.json', 'api-server/package-lock.json', 'react-frontend/package.json', 'server.js', 'lib', 'db', 'db_methods', 'wsclient']) == b'', 'Unexpected dependency, collector or persistence change')
require(result['tests_passed'] and not result['build_passed'], 'Wrong result summary')
require([item['exit'] for item in result['commands']] == [0, 0, 1], 'Unexpected command exits')
require(result['node_options'] is None, 'Unexpected Node options')
contracts = (evidence / 'contracts.stdout.txt').read_text(encoding='utf-8')
require(all(line in contracts.splitlines() for line in ['# tests 110', '# pass 110', '# fail 0', '# cancelled 0', '# skipped 0']), 'Incomplete contracts')
require((evidence / 'contracts.stderr.txt').read_bytes() == b'', 'Unexpected contract stderr')
react = (evidence / 'react-tests.stderr.txt').read_text(encoding='utf-8')
require('Tests:       6 passed, 6 total' in react and 'Test Suites: 1 passed, 1 total' in react, 'Incomplete React tests')
require(not any('Warning:' in line and 'DeprecationWarning:' not in line for line in react.splitlines()) and (evidence / 'react-tests.stdout.txt').read_bytes() == b'', 'Unexpected React rendering output')
require('ERR_OSSL_EVP_UNSUPPORTED' in (evidence / 'build.stderr.txt').read_text(encoding='utf-8'), 'Expected build blocker missing')
require('ERR_OSSL_EVP_UNSUPPORTED' in (evidence / 'build-before.txt').read_text(encoding='utf-8'), 'Inherited build failure missing')
earlier = json.loads((evidence / 'before-zero-display-review/result.json').read_text(encoding='utf-8'))
reviewed = ['react-frontend/src/snapshot-polling.js', 'react-frontend/src/Components/Main.js', 'react-frontend/src/App.test.js']
for name, digest in earlier['source_sha256'].items():
    if name in reviewed:
        data = (evidence / 'before-zero-display-review' / Path(name).name).read_bytes()
        require(hashlib.sha256(data).hexdigest() == digest, 'Archived reviewed source differs')
    else:
        require(result['source_sha256'][name] == digest, 'Unexpected final source change')
original = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'Node telemetry changed')
summary = {
    'evidence_verified': True, 'dashboard_commit': commit['dashboard_commit'],
    'contracts_passed': 110, 'react_dom_tests_passed': 6,
    'production_build_passed': False, 'build_blocker': 'webpack 4.41.0 / Node 22.11.0 ERR_OSSL_EVP_UNSUPPORTED',
    'dependency_locks_unchanged': True, 'original_dashboard_checkout_unchanged': True,
    'node_telemetry_source_unchanged': True, 'public_dashboard_ready': False,
    'remaining': ['Reviewed build-tool/runtime correction and compiled browser acceptance', 'Collector limits and per-node freshness', 'Actual efsn/RPC comparison', 'Production dependencies, supervision and TLS'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
