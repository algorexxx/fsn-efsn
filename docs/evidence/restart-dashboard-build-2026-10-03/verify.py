import hashlib
import json
from pathlib import Path
import socket
import subprocess
from urllib.parse import urlparse

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
commit = json.loads((evidence / 'commit.json').read_text(encoding='utf-8'))
result = json.loads((evidence / 'attempt-4/result.json').read_text(encoding='utf-8'))
dashboard = Path(result['dashboard_directory'])
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def require(condition, message):
    if not condition:
        raise ValueError(message)


require(subprocess.check_output(git + ['rev-parse', commit['dashboard_commit'] + '^'], text=True).strip() == commit['base'], 'Unexpected ancestry')
requests = ''.join(commit['dashboard_commit'] + ':' + name + '\n' for name in result['source_sha256'])
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests.encode())
offset = 0
for name, digest in result['source_sha256'].items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    require(len(metadata) == 3 and metadata[1] == b'blob', 'Missing committed source: ' + name)
    size = int(metadata[2])
    data = blobs[end + 1:end + 1 + size]
    require(hashlib.sha256(data).hexdigest() == digest, 'Tested source differs: ' + name)
    offset = end + size + 2
patch = (evidence / 'dashboard-build.patch').read_bytes()
require(hashlib.sha256(patch).hexdigest() == commit['patch_sha256'], 'Patch hash differs')
require(patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit['dashboard_commit']]), 'Patch differs from commit')
require(subprocess.check_output(git + ['diff', commit['base'], commit['dashboard_commit'], '--', 'package-lock.json', 'api-server/package-lock.json', 'api-server', 'server.js', 'lib', 'db', 'db_methods', 'wsclient']) == b'', 'Unexpected backend change')
for attempt, tests, build_exit in [('attempt-1', 6, 1), ('attempt-2', 6, 0), ('attempt-3', 7, 0), ('attempt-4', 7, 0)]:
    captured = json.loads((evidence / attempt / 'result.json').read_text(encoding='utf-8'))
    require([item['exit'] for item in captured['commands']] == [0, 0, build_exit], 'Unexpected exits: ' + attempt)
    require(captured['node_options'] is None, 'Unexpected Node options')
    contracts = (evidence / attempt / 'contracts.stdout.txt').read_text(encoding='utf-8')
    require(all(line in contracts.splitlines() for line in ['# tests 110', '# pass 110', '# fail 0', '# skipped 0', '# cancelled 0']), 'Incomplete contracts')
    react = (evidence / attempt / 'react-tests.stderr.txt').read_text(encoding='utf-8')
    require(f'Tests:       {tests} passed, {tests} total' in react, 'Incomplete DOM tests')
    for name, digest in captured['source_sha256'].items():
        if result['source_sha256'][name] != digest:
            copies = [evidence / old / Path(name).name for old in ['attempt-1', 'attempt-2', 'attempt-3']]
            require(any(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest for path in copies), 'Missing intermediate source: ' + attempt + '/' + name)
require((evidence / 'attempt-4/react-tests.stdout.txt').read_bytes() == b'', 'Final DOM warnings remain')
require('Compiled successfully.' in (evidence / 'attempt-4/build.stdout.txt').read_text(encoding='utf-8'), 'Final build failed')
require((evidence / 'attempt-4/build.stderr.txt').read_bytes() == b'', 'Unexpected final build stderr')
build = dashboard / 'react-frontend/build'
assets = {path.relative_to(build).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in build.rglob('*') if path.is_file()}
require(assets == result['build_sha256'], 'Compiled assets differ from tested build')
browser = json.loads((evidence / 'browser-result.json').read_text(encoding='utf-8'))
require(browser['passed'] and browser['errors'] == [] and browser['foreignRequests'] == [], 'Browser failures')
require([item['name'] for item in browser['results']] == ['populated', 'keyboard-pin', 'map', 'empty', 'storage-failure', 'recovered', 'expired-storage', 'request-timeout', 'timeout-recovery'], 'Incomplete browser scenarios')
require(browser['results'][2] == {'name': 'map', 'rendered': True, 'accessible': True, 'reportedNodeMarkers': 2}, 'Map acceptance missing')
require(len(browser['failedRequests']) == 1 and browser['failedRequests'][0]['error'] == 'net::ERR_ABORTED', 'Unexpected network failure')
require(all(item['status'] in [200, 503] for item in browser['responses']), 'Unexpected HTTP response')
require((evidence / 'browser-check.stderr.txt').read_bytes() == b'', 'Browser check error output')
process = json.loads((evidence / 'browser-process.json').read_text(encoding='utf-8'))
server = [json.loads(line) for line in (evidence / 'browser.stdout.txt').read_text(encoding='utf-8').splitlines() if line]
require(process['exit'] == 0 and server[-1]['stopped'], 'Fixture did not stop')
require(all(server[-1]['counts'][mode] > 0 for mode in ['ready', 'empty', 'unavailable', 'expired', 'hanging']), 'Missing real API mode')
require(server[0]['url'] == browser['url'], 'Browser/server address mismatch')
address = urlparse(browser['url'])
require(address.hostname == '127.0.0.1', 'Unexpected listener host')
with socket.socket() as connection:
    connection.settimeout(5)
    require(connection.connect_ex((address.hostname, address.port)) in [10061, 111], 'Listener not confirmed closed')
original = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    require(hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() == digest, 'Original source changed')
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
require(hashlib.sha256(status).hexdigest() == original['git_status_sha256'], 'Original status changed')
require(hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest() == original['efsn_ethstats_sha256'], 'Node telemetry changed')
summary = {
    'evidence_verified': True, 'dashboard_commit': commit['dashboard_commit'],
    'contracts_passed': 110, 'react_dom_tests_passed': 7, 'compiled_browser_checkpoints_passed': 9,
    'strict_production_build_passed': True, 'build_assets_matched': len(assets),
    'browser': browser['browser'], 'fixture_stopped': True,
    'backend_unchanged': True, 'original_checkout_unchanged': True,
    'public_dashboard_ready': False,
    'remaining': ['Collector limits and per-node freshness', 'Actual efsn/RPC comparison', 'Production dependencies/runtime, supervision and TLS'],
}
(evidence / 'checks.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
