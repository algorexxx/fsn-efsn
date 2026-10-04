import json
import os
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
base = Path('/home/rehearsal/results/restart-release-jwt-2026-10-04/node')
selected = Path('/home/rehearsal/results/restart-release-selection-2026-10-04')
environment = dict(os.environ, PATH=str(selected / 'toolchain/go/bin') + ':/usr/bin:/bin',
                   GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                   GOFLAGS='-mod=readonly', CGO_ENABLED='1', GOAMD64='v1', GOMAXPROCS='2',
                   GOCACHE=str(selected / 'repeat-cache'))
command = ['go', 'test', '-race', '-p=2', '-count=1', '-timeout=60s', '-run', '^TestServer$', '-v', './rpc']
with (evidence / 'baseline-rpc-server-verified.txt').open('x', encoding='utf-8') as output:
    result = subprocess.run(command, cwd=base, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=90)
(evidence / 'baseline-rpc-server-verified-exit.txt').write_text(str(result.returncode) + '\n', encoding='utf-8')
assert result.returncode == 1
assert "where'd my testdata go?" in (evidence / 'baseline-rpc-server-verified.txt').read_text(encoding='utf-8')
assert not (base / 'rpc/testdata').exists()
print(json.dumps({'expected_inherited_failure': True, 'exit': result.returncode}))
