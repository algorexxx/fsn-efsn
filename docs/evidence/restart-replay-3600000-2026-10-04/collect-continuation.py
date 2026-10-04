from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

evidence = Path(__file__).resolve().parent
stage = sys.argv[1]
assert stage in ('stopped', 'resume-preflight-refused', 'resume-startup', 'resume-final')
folder = stage if stage in ('stopped', 'resume-preflight-refused') else 'resume'
suffix = '' if stage == 'stopped' else '-resume' if stage == 'resume-preflight-refused' else '-resume-v2'
results = Path('/home/rehearsal/results/restart-replay-3600000' + suffix + '-2026-10-04')
destination = evidence / folder
destination.mkdir(exist_ok=True)
capture = destination / (stage + '-capture.json')
assert not capture.exists()
if stage == 'resume-preflight-refused':
    assert not (results / 'started.txt').exists() and not (results / 'replay.txt').exists()
    assert 'closed replay inspection requires a read-only mount' in (results / 'checkpoint-cold-check.txt').read_text()
    names = ['isolation.txt', 'capacity-before.txt', 'checkpoint-cold-check.txt']
elif stage == 'stopped':
    assert (results / 'exit-code.txt').read_text().strip() == '1'
    assert (results / 'stopped-cold-exit.txt').read_text().strip() == '0'
    assert 'closed replay matched: height=3521056 ' in (results / 'stopped-cold-check.txt').read_text()
    names = ['exit-code.txt', 'finished.txt', 'size.txt', 'allocated-size.txt', 'capacity-after.txt',
             'allocated-size-progress.txt', 'size-monitor-errors.txt', 'replay.txt',
             'stopped-cold-check.txt', 'stopped-cold-exit.txt', 'stopped-isolation.txt', 'stopped-allocated-size.txt']
elif stage == 'resume-startup':
    assert 'replay starting at height=3521056 ' in (results / 'replay.txt').read_text()
    names = ['started.txt', 'isolation.txt', 'capacity-before.txt', 'checkpoint-cold-check.txt']
    (destination / 'startup-replay-progress.txt').write_bytes((results / 'replay.txt').read_bytes())
else:
    assert (results / 'exit-code.txt').read_text().strip() == '0'
    assert (results / 'verified.txt').exists()
    cold = (results / 'final-cold-check.txt').read_text()
    assert 'closed replay matched: height=3600000 ' in cold and cold.rstrip().endswith('PASS')
    names = ['exit-code.txt', 'finished.txt', 'verified.txt', 'size.txt', 'allocated-size.txt', 'capacity-after.txt',
             'allocated-size-progress.txt', 'size-monitor-errors.txt', 'replay.txt', 'final-cold-check.txt']
for name in names:
    path = destination / name
    assert not path.exists()
    path.write_bytes((results / name).read_bytes())
if stage == 'stopped':
    (destination / 'stop-request.txt').write_bytes(Path('/home/rehearsal/replay/STOP-baseline-mainnet-3600000').read_bytes())
data = {'captured_at': datetime.now(timezone.utc).isoformat(), 'stage': stage,
        'range_completion_claim': stage == 'resume-final',
        'linux_free_gib': round(shutil.disk_usage('/').free / 1024**3, 2),
        'host_free_gib': round(shutil.disk_usage('/mnt/d').free / 1024**3, 2)}
capture.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
files = sorted(path for path in evidence.rglob('*') if path.is_file() and path.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(evidence).as_posix() + '\n' for path in files), encoding='utf-8')
print(json.dumps(data))
