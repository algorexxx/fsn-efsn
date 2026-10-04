#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-selection-2026-10-04"
work=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$work"
python3 - <<'PY'
import shutil
assert shutil.disk_usage('/home/rehearsal').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
mkdir -p "$work/toolchain" "$work/source" "$work/bin" "$work/cache" "$work/tmp"
df -B1 --output=source,size,used,avail / /mnt/d > "$evidence/capacity-before.txt"
curl --fail --location --proto '=https' --proto-redir '=https' --connect-timeout 20 --max-time 60 'https://go.dev/dl/?mode=json' -o "$evidence/go-releases.json" 2> "$evidence/metadata-download.txt"
python3 - "$evidence" <<'PY'
import json
from pathlib import Path
import sys
evidence = Path(sys.argv[1])
releases = json.loads((evidence / 'go-releases.json').read_text(encoding='utf-8'))
release = next(r for r in releases if r['version'] == 'go1.27.1' and r['stable'])
item = next(f for f in release['files'] if f['filename'] == 'go1.27.1.linux-amd64.tar.gz')
assert item['sha256'] == '63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445'
assert item['size'] == 70553950
(evidence / 'selected-toolchain.json').write_text(json.dumps(item, indent=2) + '\n', encoding='utf-8')
PY
curl --fail --location --proto '=https' --proto-redir '=https' --connect-timeout 20 --max-time 300 'https://go.dev/dl/go1.27.1.linux-amd64.tar.gz' -o "$work/toolchain/go1.27.1.linux-amd64.tar.gz" 2> "$evidence/archive-download.txt"
python3 - "$evidence" "$work" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
evidence, work = map(Path, sys.argv[1:])
item = json.loads((evidence / 'selected-toolchain.json').read_text(encoding='utf-8'))
archive = work / 'toolchain' / item['filename']
assert archive.stat().st_size == item['size']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == item['sha256']
print('PASS official toolchain archive size and SHA-256')
PY
tar -xzf "$work/toolchain/go1.27.1.linux-amd64.tar.gz" -C "$work/toolchain"
"$work/toolchain/go/bin/go" version > "$evidence/toolchain-version.txt"
date -u +%FT%TZ > "$evidence/prepared.txt"
