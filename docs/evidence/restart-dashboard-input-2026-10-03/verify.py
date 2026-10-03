import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
repository = bundle.parents[2]
commit = json.loads((bundle / 'commit.json').read_text(encoding='utf-8'))
capture = json.loads((bundle / 'capture.json').read_text(encoding='utf-8'))
dashboard = Path(capture['dashboard_directory'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^']).decode().strip() == commit['base'] == capture['base'], 'Unexpected dashboard ancestry')
patch = (bundle / 'dashboard-input.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
sources = json.loads((bundle / 'attempt-4/source-sha256.json').read_text(encoding='utf-8'))
requests = ''.join(commit['dashboard_commit'] + ':' + name + '\n' for name in sources)
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode('utf-8'))
offset = 0
for name, digest in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    require(len(metadata) == 3 and metadata[1] == b'blob', 'Missing committed source: ' + name)
    size = int(metadata[2])
    data = blobs[end + 1:end + 1 + size]
    require(hashlib.sha256(data).hexdigest() == digest, 'Tested bytes differ from commit: ' + name)
    offset = end + size + 2
for attempt, exits in [('attempt-1', [0, 1]), ('attempt-2', [0, 1]), ('attempt-3', [0, 0]), ('attempt-4', [0, 0])]:
    result = json.loads((bundle / attempt / 'results.json').read_text(encoding='utf-8'))
    require([item['exit_code'] for item in result['results']] == exits, 'Unexpected result: ' + attempt)
for label, count in [('test', 120), ('test-wire', 8)]:
    output = (bundle / 'attempt-4' / (label + '.stdout.txt')).read_text(encoding='utf-8')
    require(f'# tests {count}\n' in output and f'# pass {count}\n' in output and '# fail 0\n' in output and '# cancelled 0\n' in output, 'Wrong final test counts')
for name, digest in capture['inspected_sha256'].items():
    require(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest, 'Inspected dependency/history bytes changed: ' + name)
for name in ['lib/history.js', 'lib/collection.js']:
    current = (dashboard / name).read_bytes().replace(b'\r\n', b'\n')
    upstream = subprocess.check_output(git + ['show', 'e2049634802d4a49adadf998853ce6ee6b1158d0:' + name]).replace(b'\r\n', b'\n')
    require(current == upstream, 'History probe source differs from upstream')
for name in ['package-lock.json', 'react-frontend/package-lock.json']:
    require(subprocess.check_output(git + ['show', commit['base'] + ':' + name]) == (dashboard / name).read_bytes(), 'Dependency lock changed')
probe = [json.loads(line) for line in (bundle / 'history-probe.stdout.txt').read_text(encoding='utf-8').splitlines()]
require(probe[0]['storedHeights'] == [100], 'Unexpected advancing-head reproduction')
require(probe[1]['storedHeights'] == list(range(100, 50, -1)) and probe[1]['chartHeights'] == list(range(51, 91)), 'Unexpected chart-window reproduction')
original = json.loads((bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed: ' + name)
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original checkout status changed')
require(hashlib.sha256((repository / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'efsn telemetry source changed')
result = {'verified': True, 'dashboard_commit': commit['dashboard_commit'], 'tested_source_files': len(sources), 'contracts_passed': 120, 'socket_tests_passed': 8, 'history_probe_is_upstream_code': True, 'dependency_locks_unchanged': True, 'original_checkout_unchanged': True, 'efsn_ethstats_unchanged': True}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
