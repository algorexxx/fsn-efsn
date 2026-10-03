import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
dashboard = root / 'tmp/fsn-stats-auth'
git = ['git', '-C', str(dashboard), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
assert base == 'b94e16cbf9527c42a4797e9590c407d7c521ec13'
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-presentation.patch').write_bytes(patch)
runtime = root / 'tmp/dashboard-linux-runtime'
files = {'linux_node_archive': runtime / 'node-v22.11.0-linux-x64.tar.xz', 'linux_node': runtime / 'node-v22.11.0-linux-x64/bin/node', 'windows_node': Path('C:/Program Files/nodejs/node.exe'), 'efsn_test_binary': root / 'tmp/dashboard-presentation-tests'}
record = {'dashboard_commit': commit, 'base': base, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'artifacts': {name: {'path': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in files.items()}, 'linux_node_archive_source': 'https://nodejs.org/dist/v22.11.0/node-v22.11.0-linux-x64.tar.xz', 'checksum_source': 'https://nodejs.org/dist/v22.11.0/SHASUMS256.txt'}
assert record['artifacts']['linux_node_archive']['sha256'] == '83bf07dd343002a26211cf1fcd46a9d9534219aad42ee02847816940bf610a72'
(bundle / 'node-shasums.txt').write_bytes((runtime / 'SHASUMS256.txt').read_bytes())
(bundle / 'commit.json').write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'dashboard_commit': commit, 'base': base}))
