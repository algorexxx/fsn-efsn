import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
dashboard = bundle.parents[2] / 'tmp/fsn-stats-auth'
paths = ['server.js', 'lib/deployment-config.js', 'node_modules/primus/spark.js', 'node_modules/primus/transformers/websockets/server.js', 'node_modules/ws/lib/WebSocket.js', 'node_modules/ws/lib/Sender.js', 'package-lock.json']
with (bundle / 'probe-buffer.stdout.txt').open('wb') as output, (bundle / 'probe-buffer.stderr.txt').open('wb') as error:
    result = subprocess.run(['C:/Program Files/nodejs/node.exe', str(bundle / 'probe-buffer.cjs')], stdout=output, stderr=error, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
capture = {'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dashboard).decode().strip(), 'probe_exit': result.returncode, 'source_sha256': {name: hashlib.sha256((dashboard / name).read_bytes()).hexdigest() for name in paths}}
(bundle / 'baseline.json').write_text(json.dumps(capture, indent=2) + '\n', encoding='utf-8')
print(json.dumps(capture))
