import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
dashboard = workspace / 'tmp/fsn-stats-auth'
attempt = sys.argv[1]
if not re.fullmatch(r'attempt-[1-9][0-9]*', attempt):
    raise ValueError('Explicit unused attempt-N required')
output = evidence / attempt
output.mkdir()
(output / 'run.py').write_bytes(Path(__file__).read_bytes())
names = [
    'server.js', 'lib/telemetry-credentials.js', 'package.json', 'package-lock.json',
    '.gitignore', 'README.md', 'docs/telemetry-enrollment.md',
    'test/collector.test.cjs', 'test/telemetry-credentials.test.cjs',
    'test/telemetry-wire.test.cjs', 'test/fixtures/collector.cjs',
    'test/fixtures/wire-server.cjs',
]
sources = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names}
baseline = json.loads((evidence.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
original = Path(baseline['dashboard_directory'])
assert all(hashlib.sha256((original / name).read_bytes()).hexdigest() == digest for name, digest in baseline['dashboard_source_sha256'].items())
original_status = subprocess.check_output(['git', '-C', str(original), '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
assert hashlib.sha256(original_status).hexdigest() == baseline['git_status_sha256']
commands = [
    ('syntax-server', ['node', '--check', 'server.js']),
    ('syntax-credentials', ['node', '--check', 'lib/telemetry-credentials.js']),
    ('contracts', ['node', '--test', '--test-reporter=tap', 'test/collector.test.cjs', 'test/telemetry-credentials.test.cjs']),
    ('wire', ['node', '--test', '--test-reporter=tap', 'test/telemetry-wire.test.cjs']),
]
results = []
for name, command in commands:
    result = subprocess.run(command, cwd=dashboard, capture_output=True, timeout=45)
    (output / (name + '.txt')).write_bytes(result.stdout)
    (output / (name + '-stderr.txt')).write_bytes(result.stderr)
    results.append({'name': name, 'command': command, 'exit': result.returncode})
    print(name, 'exit', result.returncode)
    if result.returncode:
        print(result.stdout.decode('utf-8'))
        print(result.stderr.decode('utf-8'))
versions = {}
for name in ['primus', 'primus-emit', 'primus-spark-latency', 'ws', 'lodash', 'geoip-lite']:
    versions[name] = json.loads((dashboard / 'node_modules' / name / 'package.json').read_text(encoding='utf-8'))['version']
require_unchanged = all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in sources.items())
assert require_unchanged
summary = {
    'dashboard_worktree': str(dashboard),
    'dashboard_branch': subprocess.check_output(['git', '-C', str(dashboard), 'branch', '--show-current'], text=True).strip(),
    'dashboard_baseline': baseline['dashboard_head'],
    'efsn_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=workspace, text=True).strip(),
    'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
    'dependency_versions': versions,
    'source_sha256': sources,
    'commands': results,
    'original_source_and_status_unchanged': True,
    'candidate_sources_unchanged_by_tests': True,
    'all_exits_zero': all(item['exit'] == 0 for item in results),
    'scope': 'Handler/credential contracts and real pinned collector/collection/WebSocket plugins; synthetic clients; child listener forced to 127.0.0.1 and an ephemeral port. No chain node, PostgreSQL, HTTP read API, browser, TLS or public deployment.',
}
(output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
sys.exit(0 if summary['all_exits_zero'] else 1)
