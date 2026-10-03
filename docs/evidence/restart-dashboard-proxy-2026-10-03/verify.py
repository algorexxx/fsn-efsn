import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = read(bundle / 'commit.json')
commit = record['dashboard_commit']
assert record['base'] == '63d1b14df79aa01f8bf16e2338fc510d753b1a97'
assert subprocess.check_output(git + ['rev-parse', commit + '^']).decode().strip() == record['base']
patch = (bundle / 'dashboard-proxy.patch').read_bytes()
assert hashlib.sha256(patch).hexdigest() == record['patch_sha256']
assert patch == subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
changed = set(subprocess.check_output(git + ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]).decode().splitlines())
assert changed == {'deploy/nginx.conf.template', 'docs/proxy-tls.md', 'docs/deployment-configuration.md', 'test/collector-input-wire.test.cjs', 'test/fixtures/wire-client.cjs', 'test/fixtures/proxy-wire-server.cjs', 'test/fixtures/nginx.cjs', 'test/proxy-tls.test.cjs'}
wire = read(bundle / 'wire-1/result.json')
sources = wire['source_sha256']
tracked = subprocess.check_output(git + ['ls-tree', '-r', '--name-only', commit]).decode().splitlines()
assert set(sources) == {name for name in tracked if not name.endswith('.md')}
requests = ''.join(commit + ':' + name + '\n' for name in sources).encode()
blobs = subprocess.check_output(git + ['cat-file', '--batch'], input=requests)
offset = 0
for name, value in sources.items():
    end = blobs.index(b'\n', offset)
    metadata = blobs[offset:end].split()
    assert metadata[1] == b'blob'
    size = int(metadata[2])
    assert hashlib.sha256(blobs[end + 1:end + 1 + size]).hexdigest() == value, name
    assert digest(dashboard / name) == value, name
    offset = end + size + 2
assert wire['runner_sha256'] == digest(bundle / 'run-wire.py')
assert wire['results'] == [{'platform': 'linux', 'exit': 0}, {'platform': 'windows', 'exit': 0}]
for platform in ['linux', 'windows']:
    assert '# pass 13\n# fail 0\n' in (bundle / f'wire-1/{platform}.stdout.txt').read_text(encoding='utf-8')
    assert read(bundle / f'{platform}-process-cleanup.json') == {'remaining_test_processes': [], 'count': 0}
final = read(bundle / 'attempt-3/result.json')
assert final['passed'] is False
commands = {item['name']: item['exit'] for item in final['commands']}
assert commands['proxy-test'] == 0 and commands['wire-tests'] == 1
assert '# pass 1\n# fail 0\n' in (bundle / 'attempt-3/proxy-test.stdout.txt').read_text(encoding='utf-8')
assert '# pass 12\n# fail 1\n' in (bundle / 'attempt-3/wire-tests.stdout.txt').read_text(encoding='utf-8')
assert final['source_sha256'].keys() == sources.keys()
for name, value in sources.items():
    expected = hashlib.sha256(subprocess.check_output(git + ['show', record['base'] + ':' + name])).hexdigest() if name == 'test/collector-input-wire.test.cjs' else value
    assert final['source_sha256'][name] == expected, name
for index in range(1, 4):
    attempt = bundle / f'attempt-{index}'
    run = read(attempt / 'result.json')
    assert run['runner_sha256'] == digest(bundle / 'run.py')
    assert run['private_removed'] and run['passed'] is False
    for proxy in ['active', 'idle']:
        assert read(attempt / proxy / 'process.json')['result'] == [0, None]
    if index < 3:
        assert '# pass 0\n# fail 1\n' in (attempt / 'proxy-test.stdout.txt').read_text(encoding='utf-8')
    assert run['build_sha256'] == final['build_sha256']
    for name, value in run['runtime_sha256'].items():
        assert digest(root / name) == value
    for name, value in run['dependency_sha256'].items():
        assert digest(dashboard / name) == value
data = read(bundle / 'attempt-3/proxy.json')
assert data['errors'] == [] and len(data['forwardedHeaders']) == 8
assert data['checks'] == dict.fromkeys(['certificateTrustAndHostname', 'compiledAssets', 'routeIsolation', 'staleSnapshotUnavailable', 'reporterConnectionLimit', 'authentication', 'complete'], True)
assert data['historyBytes'] == 3276956 and max(item['bytes'] for item in data['saves']) == 554505
assert [item['bytes'] for item in data['requests'] if 'bytes' in item] == [588759, 549890, 17809, 9418]
assert sum(item['status'] == 404 for item in data['requests']) == 20
assert data['heartbeatCount'] == 24 and data['activeDurationMs'] == 48113
assert [data[name] for name in ['apiTimeoutMs', 'helloTimeoutMs', 'idleTimeoutMs']] == [5005, 5003, 45884]
assert all(item['headers']['x-forwarded-for'] == '127.0.0.1' for item in data['forwardedHeaders'])
for name, value in record['dependency_sha256'].items():
    assert digest(dashboard / name) == value
assert digest(Path('C:/Program Files/nodejs/node.exe')) == record['windows_node_sha256']
previous = bundle.parent / 'restart-dashboard-enrollment-2026-10-03/attempt-4'
assert final['build_sha256'] == read(previous / 'result.json')['build_sha256']
for name, value in final['build_sha256'].items():
    assert digest(dashboard / 'react-frontend/build' / name) == value
efsn_sources = read(previous / 'efsn-source-sha256.json')
for name, value in efsn_sources.items():
    assert digest(root / name) == value
original = read(bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json')
for name, value in original['dashboard_source_sha256'].items():
    assert digest(Path(original['dashboard_directory']) / name) == value
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(status).hexdigest() == original['git_status_sha256']
result = {'verified': True, 'dashboard_commit': commit, 'deployment_change': 'deploy/nginx.conf.template', 'application_code_changes': 0, 'dashboard_non_markdown_sources': len(sources), 'unchanged_efsn_go_and_module_sources': len(efsn_sources), 'unchanged_frontend_build_files': len(final['build_sha256']), 'proxy_test_passed': True, 'wire_tests_passed_per_platform': 13, 'remaining_test_processes': 0, 'original_dashboard_preserved': True, 'public_deployment_approved': False}
(bundle / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result, indent=2))
