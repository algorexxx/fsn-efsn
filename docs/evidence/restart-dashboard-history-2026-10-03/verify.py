import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
repository = bundle.parents[2]
dashboard = repository / 'tmp/fsn-stats-auth'
commit = json.loads((bundle / 'commit.json').read_text(encoding='utf-8'))
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


require(commit['base'] == 'f0c87459d0c64a2703714dd236d2a83f10247089', 'Unexpected base')
require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base'], 'Unexpected ancestry')
patch = (bundle / 'dashboard-history.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
sources = json.loads((bundle / 'attempt-2/source-sha256.json').read_text(encoding='utf-8'))
sources = {name: digest for name, digest in sources.items() if not name.lower().endswith('.md')}
requests = ''.join(commit['dashboard_commit'] + ':' + name + '\n' for name in sources)
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode('utf-8'))
offset = 0
for name, digest in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    require(len(metadata) == 3 and metadata[1] == b'blob', 'Missing source: ' + name)
    size = int(metadata[2])
    data = blobs[end + 1:end + 1 + size]
    require(hashlib.sha256(data).hexdigest() == digest, 'Tested source differs: ' + name)
    offset = end + size + 2
baseline = json.loads((bundle / 'baseline/source-sha256.json').read_text(encoding='utf-8'))
for name in ['lib/history.js', 'lib/collection.js', 'server.js', 'package.json']:
    require(hashlib.sha256(subprocess.check_output(git + ['show', commit['base'] + ':' + name])).hexdigest() == baseline[name], 'Baseline source differs: ' + name)
baseline_output = (bundle / 'baseline/history-baseline.stdout.txt').read_text(encoding='utf-8')
require('# tests 13\n' in baseline_output and '# fail 13\n' in baseline_output, 'Wrong baseline count')
for attempt in ['attempt-1', 'attempt-2']:
    result = json.loads((bundle / attempt / 'results.json').read_text(encoding='utf-8'))
    require(all(item['exit_code'] == 0 for item in result['results']), 'Failed run: ' + attempt)
    for label, count in [('test', 145), ('test-wire', 10)]:
        output = (bundle / attempt / (label + '.stdout.txt')).read_text(encoding='utf-8')
        require(all(f'# {key} {value}\n' in output for key, value in [('tests', count), ('pass', count), ('fail', 0), ('cancelled', 0), ('skipped', 0)]), 'Wrong test counts')
database = json.loads((bundle / 'attempt-3/result.json').read_text(encoding='utf-8'))
require(database['expected_outcome_passed'] and database['password_file_removed'], 'Database run/cleanup failed')
require([item['exit'] for item in database['commands']] == [0, 0, 0, 0, 0, 3], 'Unexpected database command result')
for name, digest in database['source_sha256'].items():
    require(sources[name] == digest, 'Database-tested source differs: ' + name)
output = (bundle / 'attempt-3/persistence.txt').read_text(encoding='utf-8')
require('# tests 7\n' in output and '# pass 7\n' in output and '# fail 0\n' in output, 'Wrong database scenario count')
require(not (Path(database['scratch_directory']) / 'password.txt').exists(), 'Database password file remains')
require(not (Path(database['scratch_directory']) / 'data/postmaster.pid').exists(), 'Database is not stopped')
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit['dashboard_commit']]).decode().splitlines())
require(changed == {'lib/history.js', 'lib/collection.js', 'server.js', 'package.json', 'test/history.test.cjs', 'test/history-wire.test.cjs', 'test/persistence.test.cjs', 'docs/chart-history.md'}, 'Unexpected candidate scope')
for name in ['package-lock.json', 'react-frontend/package-lock.json']:
    require(subprocess.check_output(git + ['show', commit['base'] + ':' + name]) == (dashboard / name).read_bytes(), 'Dependency lock changed')
require(subprocess.check_output(git + ['diff', '--name-only', commit['base'], commit['dashboard_commit'], '--', 'react-frontend']) == b'', 'Frontend changed')
original = json.loads((bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original checkout changed')
require(hashlib.sha256((repository / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'efsn telemetry changed')
cleanup = json.loads((bundle / 'process-cleanup.json').read_text(encoding='utf-8'))
require(cleanup['count'] == 0 and cleanup['remaining_test_processes'] == [], 'Test processes remain')
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'tested_non_markdown_source_files': len(sources), 'contracts': 145, 'socket_tests': 10, 'postgres_scenarios': 6, 'postgres_stopped': True, 'baseline_history_failures': 13, 'dependency_locks_unchanged': True, 'frontend_unchanged': True, 'original_checkout_unchanged': True, 'efsn_ethstats_unchanged': True, 'remaining_test_processes': 0}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
