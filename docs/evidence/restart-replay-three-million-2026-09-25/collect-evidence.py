from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parent
results = Path('/home/rehearsal/results/restart-replay-three-million-2026-09-25')
target = Path('/home/rehearsal/replay/baseline-mainnet-three-million')
stage = sys.argv[1]
assert stage in ['startup', 'final'], 'choose startup or final'
assert not (evidence / (stage + '-capture.json')).exists(), 'capture already exists'
files = ['copy-manifest.json', 'copy-verified.txt', 'checkpoint-cold-check.txt', 'isolation.txt', 'capacity-before.txt', 'started.txt']
if stage == 'final':
    assert (results / 'exit-code.txt').read_text(encoding='utf-8').strip() == '0', 'replay did not pass'
    assert 'closed replay matched: height=3000000 ' in (results / 'final-cold-check.txt').read_text(encoding='utf-8'), 'exact-height check absent'
    assert (results / 'final-cold-check.txt').read_text(encoding='utf-8').rstrip().endswith('PASS'), 'cold check did not pass'
    files += ['exit-code.txt', 'finished.txt', 'verified.txt', 'final-cold-check.txt', 'size.txt', 'allocated-size.txt', 'capacity-after.txt', 'allocated-size-progress.txt', 'size-monitor-errors.txt', 'replay.txt']
for name in files:
    data = (results / name).read_bytes()
    destination = evidence / name
    if destination.exists():
        assert destination.read_bytes() == data, 'existing capture differs: ' + name
    else:
        with destination.open('xb') as writer:
            writer.write(data)
if stage == 'startup':
    with (evidence / 'startup-replay-progress.txt').open('xb') as writer:
        writer.write((results / 'replay.txt').read_bytes())
identity = (target / 'replay-identity.json').read_bytes()
destination = evidence / 'replay-identity.json'
if destination.exists():
    assert destination.read_bytes() == identity
else:
    with destination.open('xb') as writer:
        writer.write(identity)
status = json.loads(subprocess.check_output(['python3', str(evidence / 'status.py')]))
capture = {'captured_at': datetime.now(timezone.utc).isoformat(), 'stage': stage, 'completion_claim': stage == 'final', 'status': status}
(evidence / (stage + '-capture.json')).write_text(json.dumps(capture, indent=2) + '\n', encoding='utf-8')
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != 'SHA256SUMS')
(evidence / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n' for path in files), encoding='utf-8')
print(f'Captured {stage} evidence and {len(files)} checksums; completion_claim={stage == "final"}')
