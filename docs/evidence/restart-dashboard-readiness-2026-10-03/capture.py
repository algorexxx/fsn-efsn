import hashlib
import json
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
dashboard = Path('C:/Users/Peter/Documents/CODING/fusionfoundation/fsn-stats')
baseline = evidence / 'baseline'
baseline.mkdir()
names = [
    'server.js', 'lib/collection.js', 'lib/node.js', 'lib/utils/config.js',
    'wsclient/wsclient.js', 'db/index.js', 'db_methods/populate.js',
    'db_methods/retrieve.js', 'api-server/server.js', 'api-server/package.json',
    'api-server/package-lock.json', 'package.json', 'package-lock.json',
    'react-frontend/package.json', 'react-frontend/package-lock.json',
    'react-frontend/src/Components/Main.js', '.github/workflows/deploy.yml',
    'README.md', 'POSTGRESQL_Setup.sh',
]
git = ['git', '-C', str(dashboard), '-c', 'core.safecrlf=false', '-c', 'core.autocrlf=false']
status_before = subprocess.check_output(git + ['status', '--porcelain', '-z'])
sources = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in names}
head_equal = {}
for name in names:
    original = subprocess.check_output(git + ['show', f'HEAD:{name}'])
    current = (dashboard / name).read_bytes()
    head_equal[name] = {
        'exact_bytes': current == original,
        'after_crlf_normalization': current.replace(b'\r\n', b'\n') == original.replace(b'\r\n', b'\n'),
    }
(baseline / 'server.js').write_bytes((dashboard / 'server.js').read_bytes())
result = subprocess.run(['node', '--test', '--test-reporter=tap', str(evidence / 'collector-contract.test.cjs')], capture_output=True)
(baseline / 'tests.tap').write_bytes(result.stdout)
(baseline / 'stderr.txt').write_bytes(result.stderr)
(baseline / 'exit.txt').write_text(str(result.returncode) + '\n', encoding='utf-8')
status_after = subprocess.check_output(git + ['status', '--porcelain', '-z'])
assert status_before == status_after, 'Dashboard worktree status changed'
assert all(hashlib.sha256((dashboard / name).read_bytes()).hexdigest() == digest for name, digest in sources.items())
metadata = {
    'dashboard_directory': str(dashboard),
    'dashboard_head': subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip(),
    'node_version': subprocess.check_output(['node', '--version'], text=True).strip(),
    'efsn_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'git_status_entries': len([item for item in status_before.split(b'\0') if item]),
    'git_status_sha256': hashlib.sha256(status_before).hexdigest(),
    'dashboard_source_sha256': sources,
    'inspected_sources_vs_head': head_equal,
    'efsn_ethstats_sha256': hashlib.sha256((workspace / 'ethstats/ethstats.go').read_bytes()).hexdigest(),
    'harness_sha256': hashlib.sha256((evidence / 'collector-contract.test.cjs').read_bytes()).hexdigest(),
    'test_exit': result.returncode,
    'source_and_status_unchanged': True,
    'scope': 'Archived collector source executed with dependency, socket, collection and timer doubles; no network, database, dependency install, production key or deployment.',
}
(evidence / 'capture.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: metadata[key] for key in ['dashboard_head', 'node_version', 'git_status_entries', 'test_exit', 'source_and_status_unchanged']}, indent=2))
print(result.stdout.decode('utf-8'))
