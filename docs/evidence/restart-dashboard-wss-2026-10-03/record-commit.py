import hashlib
import json
import subprocess
from pathlib import Path

bundle = Path(__file__).resolve().parent
root = bundle.parents[2]
git = ['git', '-C', str(root / 'tmp/fsn-stats-auth'), '-c', 'core.autocrlf=false']
commit = subprocess.check_output(git + ['rev-parse', 'HEAD']).decode().strip()
base = subprocess.check_output(git + ['rev-parse', 'HEAD^']).decode().strip()
assert base == '4ca1f59bb273569e5b82a1390e93b36e1fdd4b01'
patch = subprocess.check_output(git + ['format-patch', '-1', '--stdout', '--no-signature', commit])
(bundle / 'dashboard-wss.patch').write_bytes(patch)
record = {'dashboard_commit': commit, 'base': base, 'patch_sha256': hashlib.sha256(patch).hexdigest(), 'go_fixture_sha256': hashlib.sha256((root / 'tests/restart/dashboard_telemetry_linux_test.go').read_bytes()).hexdigest(), 'go_build_command': 'GOMAXPROCS=2 GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local /opt/fusion-toolchain/go/bin/go test -c -mod=readonly -o tmp/dashboard-tls-tests ./tests/restart'}
(bundle / 'commit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
metadata = subprocess.check_output(['wsl', '-d', 'FusionRehearsal', '-u', 'rehearsal', '--', '/opt/fusion-toolchain/go/bin/go', 'version', '-m', '/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/dashboard-tls-tests'])
(bundle / 'go-build-metadata.txt').write_bytes(metadata)
print(json.dumps({'dashboard_commit': commit, 'base': base}))
