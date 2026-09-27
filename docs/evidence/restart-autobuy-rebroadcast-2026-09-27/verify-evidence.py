import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
production = ['eth/api_backend.go', 'eth/handler.go', 'internal/ethapi/autobuy.go', 'internal/ethapi/backend.go', 'les/api_backend.go']
tests = ['internal/ethapi/autobuy_retry_test.go', 'eth/autobuy_retry_test.go', 'eth/restart_purchase_retry_test.go', 'tests/restart/autobuy_backend_test.go', 'tests/restart/full_state_delivery_linux_test.go']

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

for name in ('focused-final', 'peer-focused', 'protocol', 'node-build', 'regression-final', 'live'):
    assert (evidence / (name + '-exit.txt')).read_text().strip() == '0', name
assert (evidence / 'regression-exit.txt').read_text().strip() == '1'
live = (evidence / 'live-race.txt').read_text(encoding='utf-8')
rows = re.findall(r'participant ledger block=(\d+) .*? transactions=(\d+) retreats=(\d+);', live)
new = [(int(n), int(t), int(r)) for n, t, r in rows if 45 <= int(n) <= 52]
assert len(new) == 8 and sum(t for _, t, _ in new) == 8 and sum(r for _, _, r in new) == 0
for name in ('focused-final.txt', 'peer-focused.txt', 'protocol-race.txt', 'regression-final-race.txt', 'live-race.txt'):
    data = (evidence / name).read_text(encoding='utf-8')
    assert 'WARNING: DATA RACE' not in data and '--- FAIL:' not in data, name

identity = {
    'Baseline': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=workspace, text=True).strip(),
    'ProductionSHA256': {p: digest(workspace / p) for p in production},
    'TestSHA256': {p: digest(workspace / p) for p in tests},
    'FinalControllerRun': 'focused-final.txt',
    'FirstRegressionFailure': 'Wrong working directory; fixtures not found. Same binary rerun from tests/restart.',
    'EthTests': 'All ten production files plus named focused tests; inherited full test-package compile failure is retained in the previous evidence.',
    'NewBlockLedger': new,
}
(evidence / 'identities.json').write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8', newline='\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(evidence).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')
print(f'Verified final runs, eight new ledger blocks and {len(files)} evidence files; recorded five production-file hashes.')
