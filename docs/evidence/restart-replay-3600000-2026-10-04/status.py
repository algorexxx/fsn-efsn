from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

results = Path('/home/rehearsal/results/restart-replay-3600000-2026-10-04')
if '--resume' in sys.argv:
    results = Path('/home/rehearsal/results/restart-replay-3600000-resume-v2-2026-10-04')
status = {'time': datetime.now(timezone.utc).isoformat(), 'linux_free_gib': round(shutil.disk_usage('/').free / 1024**3, 2), 'host_free_gib': round(shutil.disk_usage('/mnt/d').free / 1024**3, 2)}
for name in ['copy-verified.txt', 'started.txt', 'exit-code.txt', 'verified.txt', 'allocated-size-progress.txt', 'checkpoint-cold-check.txt', 'replay.txt', 'final-cold-check.txt', 'size-monitor-errors.txt']:
    path = results / name
    if path.exists():
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 4096))
            status[name] = stream.read().decode('utf-8', errors='replace').splitlines()[-3:]
print(json.dumps(status, indent=2))
