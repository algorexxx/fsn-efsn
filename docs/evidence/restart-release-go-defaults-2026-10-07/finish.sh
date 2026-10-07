#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-go-defaults-2026-10-07
test ! -e "$evidence/final-verification.txt"
python3 "$evidence/report.py" --check > "$evidence/final-verification.txt"
df -B1 / /mnt/d > "$evidence/final-disk.txt"
free -b > "$evidence/final-memory.txt"
du -s -B1 /home/rehearsal/results/restart-release-go-defaults-2026-10-07 > "$evidence/final-allocation.txt"
python3 - "$evidence" <<'PY'
import hashlib
from pathlib import Path
import sys
evidence = Path(sys.argv[1])
files = sorted(p for p in evidence.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
assert not any(p.suffix == '.pyc' for p in files)
lines = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(evidence).as_posix() for p in files]
(evidence / 'SHA256SUMS').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Checksummed', len(files), 'evidence files')
PY
