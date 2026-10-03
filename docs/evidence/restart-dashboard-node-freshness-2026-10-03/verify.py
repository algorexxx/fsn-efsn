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


require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base'], 'Unexpected ancestry')
patch = (bundle / 'dashboard-node-freshness.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
sources = json.loads((bundle / 'attempt-5/source-sha256.json').read_text(encoding='utf-8'))
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
earlier = json.loads((bundle / 'attempt-3/source-sha256.json').read_text(encoding='utf-8'))
for name, digest in sources.items():
    if name != 'react-frontend/src/Components/Main.js':
        require(digest == earlier[name], 'Unexpected change after full suite: ' + name)
for attempt in ['attempt-1', 'attempt-3', 'attempt-5']:
    result = json.loads((bundle / attempt / 'results.json').read_text(encoding='utf-8'))
    require(all(item['exit_code'] == 0 for item in result['results']), 'Failed run: ' + attempt)
for label, count in [('test', 132), ('test-wire', 9)]:
    output = (bundle / 'attempt-3' / (label + '.stdout.txt')).read_text(encoding='utf-8')
    require(f'# tests {count}\n' in output and f'# pass {count}\n' in output and '# fail 0\n' in output, 'Wrong test counts')
require('8 passed, 8 total' in (bundle / 'attempt-5/react-tests.stderr.txt').read_text(encoding='utf-8'), 'Wrong DOM count')
require('Compiled successfully.' in (bundle / 'attempt-5/build.stdout.txt').read_text(encoding='utf-8'), 'Build did not pass')
build = json.loads((bundle / 'attempt-5/build-sha256.json').read_text(encoding='utf-8'))
for name, digest in build.items():
    require(hashlib.sha256((dashboard / 'react-frontend/build' / name).read_bytes()).hexdigest() == digest, 'Build asset changed: ' + name)
for attempt in ['attempt-2', 'attempt-4']:
    result = json.loads((bundle / attempt / 'result.json').read_text(encoding='utf-8'))
    require(result['expected_outcome_passed'] and result['password_file_removed'], 'Database run/cleanup failed')
    require([item['exit'] for item in result['commands']] == [0, 0, 0, 0, 0, 3], 'Unexpected database command result')
    if attempt == 'attempt-4':
        for name, digest in result['source_sha256'].items():
            require(sources[name] == digest, 'Database-tested source differs: ' + name)
        output = (bundle / attempt / 'persistence.txt').read_text(encoding='utf-8')
        require('# tests 6\n' in output and '# pass 6\n' in output, 'Wrong database scenario count')
browser = json.loads((bundle / 'browser-result.json').read_text(encoding='utf-8'))
require(browser['passed'] and len(browser['results']) == 13 and browser['errors'] == [] and browser['foreignRequests'] == [], 'Browser acceptance differs')
require(all(item['status'] != 404 for item in browser['responses']), 'Missing browser asset')
require([item['error'] for item in browser['failedRequests']] == ['net::ERR_ABORTED'], 'Unexpected failed browser request')
require(json.loads((bundle / 'browser-run.json').read_text(encoding='utf-8')) == {'browser_exit': 0, 'server_exit': 0, 'listener_probe': 10061}, 'Browser cleanup failed')
require(json.loads((bundle / 'browser.stdout.txt').read_text(encoding='utf-8').splitlines()[-1])['stopped'], 'Fixture not stopped')
for name in ['package-lock.json', 'react-frontend/package-lock.json']:
    require(subprocess.check_output(git + ['show', commit['base'] + ':' + name]) == (dashboard / name).read_bytes(), 'Dependency lock changed')
original = json.loads((bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original checkout changed')
require(hashlib.sha256((repository / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'efsn telemetry changed')
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'tested_non_markdown_source_files': len(sources), 'build_assets': len(build), 'contracts': 132, 'socket_tests': 9, 'dom_tests': 8, 'postgres_scenarios': 5, 'browser_checkpoints': 13, 'dependency_locks_unchanged': True, 'original_checkout_unchanged': True, 'efsn_ethstats_unchanged': True}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
