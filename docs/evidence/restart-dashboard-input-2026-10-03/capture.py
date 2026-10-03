import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
repository = bundle.parents[2]
dashboard = repository / 'tmp/fsn-stats-auth'
node = 'C:/Program Files/nodejs/node.exe'
with (bundle / 'history-probe.stdout.txt').open('wb') as output, (bundle / 'history-probe.stderr.txt').open('wb') as error:
    probe = subprocess.run([node, str(bundle / 'probe-history.cjs'), str(dashboard)], stdout=output, stderr=error, stdin=subprocess.DEVNULL, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
if probe.returncode != 0:
    raise ValueError('History probe failed')
original = json.loads((bundle.parent / 'restart-dashboard-readiness-2026-10-03/capture.json').read_text(encoding='utf-8'))
for name, digest in original['dashboard_source_sha256'].items():
    if hashlib.sha256((Path(original['dashboard_directory']) / name).read_bytes()).hexdigest() != digest:
        raise ValueError('Original source changed: ' + name)
status = subprocess.check_output(['git', '-C', original['dashboard_directory'], '-c', 'core.autocrlf=false', 'status', '--porcelain', '-z'])
if hashlib.sha256(status).hexdigest() != original['git_status_sha256']:
    raise ValueError('Original checkout status changed')
if hashlib.sha256((repository / 'ethstats/ethstats.go').read_bytes()).hexdigest() != original['efsn_ethstats_sha256']:
    raise ValueError('efsn telemetry changed')
versions = {name: json.loads((dashboard / 'node_modules' / name / 'package.json').read_text(encoding='utf-8'))['version'] for name in ['primus', 'ws', 'primus-emit', 'lodash']}
paths = ['lib/history.js', 'lib/collection.js', 'node_modules/primus/transformers/websockets/server.js', 'node_modules/primus/spark.js', 'node_modules/ws/lib/Receiver.js', 'node_modules/ws/lib/WebSocket.js', 'package-lock.json', 'react-frontend/package-lock.json']
hashes = {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in paths}
metadata = {'dashboard_directory': str(dashboard), 'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dashboard).decode().strip(), 'node': subprocess.check_output([node, '--version']).decode().strip(), 'dependency_versions': versions, 'history_probe_exit': probe.returncode, 'inspected_sha256': hashes, 'original_checkout_unchanged': True, 'efsn_ethstats_unchanged': True}
(bundle / 'capture.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
print(json.dumps(metadata), flush=True)
