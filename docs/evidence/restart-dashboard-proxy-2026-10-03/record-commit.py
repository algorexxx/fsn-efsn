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
assert base == '63d1b14df79aa01f8bf16e2338fc510d753b1a97'
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-proxy.patch').write_bytes(patch)
dependencies = ['node_modules/ws/lib/Receiver.js', 'node_modules/ws/lib/WebSocket.js', 'node_modules/primus/index.js', 'node_modules/primus/spark.js', 'node_modules/primus/transformer.js', 'node_modules/primus/transformers/websockets/server.js', 'node_modules/primus/middleware/forwarded.js', 'node_modules/forwarded-for/index.js']
record = {'dashboard_commit': commit, 'base': base, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'windows_node_sha256': hashlib.sha256(Path('C:/Program Files/nodejs/node.exe').read_bytes()).hexdigest(), 'dependency_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in dependencies}}
(bundle / 'commit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'dashboard_commit': commit, 'base': base}))
