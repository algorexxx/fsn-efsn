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


require(commit['base'] == '6893caa09e0db17d8b0f70a5d8349c1fb5bbb2c2', 'Unexpected base')
require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base'], 'Unexpected ancestry')
patch = (bundle / 'dashboard-output.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
sources = json.loads((bundle / 'attempt-1/source-sha256.json').read_text(encoding='utf-8'))
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
baseline = json.loads((bundle / 'baseline.json').read_text(encoding='utf-8'))
require(baseline['base'] == commit['base'] and baseline['probe_exit'] == 0, 'Baseline capture differs')
for name, digest in baseline['source_sha256'].items():
    data = (dashboard / name).read_bytes() if name.startswith('node_modules/') else subprocess.check_output(git + ['show', commit['base'] + ':' + name])
    require(hashlib.sha256(data).hexdigest() == digest, 'Inspected source differs: ' + name)
probe = json.loads((bundle / 'probe-buffer.stdout.txt').read_text(encoding='utf-8'))
require(probe['writableLength'] == 16 and probe['destroyed'] is False, 'Probe differs')
result = json.loads((bundle / 'attempt-1/results.json').read_text(encoding='utf-8'))
require(all(item['exit_code'] == 0 for item in result['results']), 'Test run failed')
for label, count in [('test', 151), ('test-wire', 12)]:
    output = (bundle / 'attempt-1' / (label + '.stdout.txt')).read_text(encoding='utf-8')
    require(all(f'# {key} {value}\n' in output for key, value in [('tests', count), ('pass', count), ('fail', 0), ('cancelled', 0), ('skipped', 0)]), 'Wrong test counts')
wire = (bundle / 'attempt-1/test-wire.stdout.txt').read_text(encoding='utf-8')
measurements = [json.loads(line[2:]) for line in wire.splitlines() if line.startswith('# {')]
require(len(measurements) == 4, 'Missing output measurements')
for measurement in measurements:
    limit = 512 if 'endpoint' in measurement else 8192
    require(measurement['held']['queued'] > 0 and measurement['stopped']['peak'] <= limit and measurement['stopped']['queued'] == 0 and measurement['stopped']['destroyed'], 'Output did not remain bounded')
database = json.loads((bundle / 'attempt-2/result.json').read_text(encoding='utf-8'))
require(database['expected_outcome_passed'] and database['password_file_removed'], 'Database run/cleanup failed')
require([item['exit'] for item in database['commands']] == [0, 0, 0, 0, 0, 3], 'Unexpected database command result')
for name, digest in database['source_sha256'].items():
    require(sources[name] == digest, 'Database-tested source differs: ' + name)
output = (bundle / 'attempt-2/persistence.txt').read_text(encoding='utf-8')
require('# tests 7\n' in output and '# pass 7\n' in output and '# fail 0\n' in output, 'Wrong database scenario count')
require(not (Path(database['scratch_directory']) / 'password.txt').exists(), 'Database password file remains')
require(not (Path(database['scratch_directory']) / 'data/postmaster.pid').exists(), 'Database is not stopped')
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit['dashboard_commit']]).decode().splitlines())
expected = {'docs/chart-history.md', 'docs/collector-input-limits.md', 'docs/deployment-configuration.md', 'docs/collector-output-limits.md', 'lib/collector-output.js', 'lib/deployment-config.js', 'server.js', 'package.json', 'test/collector-input.test.cjs', 'test/collector-output.test.cjs', 'test/collector-output-wire.test.cjs', 'test/fixtures/collector.cjs', 'test/fixtures/collector-environment.cjs', 'test/fixtures/collector-wire.cjs', 'test/fixtures/output-wire-server.cjs'}
require(changed == expected, 'Unexpected candidate scope')
for name in ['package-lock.json', 'react-frontend/package-lock.json']:
    require(subprocess.check_output(git + ['show', commit['base'] + ':' + name]) == (dashboard / name).read_bytes(), 'Dependency lock changed')
require(subprocess.check_output(git + ['diff', '--name-only', commit['base'], commit['dashboard_commit'], '--', 'react-frontend', 'db', 'db_methods']) == b'', 'Frontend or persistence changed')
original = json.loads((bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original checkout changed')
require(hashlib.sha256((repository / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'efsn telemetry changed')
cleanup = json.loads((bundle / 'process-cleanup.json').read_text(encoding='utf-8'))
require(cleanup['count'] == 0 and cleanup['remaining_test_processes'] == [], 'Test processes remain')
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'tested_non_markdown_source_files': len(sources), 'contracts': 151, 'socket_tests': 12, 'postgres_scenarios': 6, 'postgres_stopped': True, 'bounded_output_measurements': measurements, 'dependency_locks_unchanged': True, 'frontend_unchanged': True, 'original_checkout_unchanged': True, 'efsn_ethstats_unchanged': True, 'remaining_test_processes': 0}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'bounded_output_measurements'}))
