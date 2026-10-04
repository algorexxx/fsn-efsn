#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-selection-2026-10-04"
extraction="$workspace/docs/evidence/restart-release-extraction-2026-10-04"
inputs="$workspace/tmp/release-extraction-2026-10-04-exact"
work=/home/rehearsal/results/restart-release-selection-2026-10-04
test -s "$evidence/prepared.txt"
test ! -e "$evidence/build-started.txt"
test -z "$(ls -A "$work/source")"
export PATH="$work/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2
export GOCACHE="$work/cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
python3 - "$extraction" "$inputs" <<'PY'
import hashlib
import json
from pathlib import Path
import shutil
import sys
evidence, inputs = map(Path, sys.argv[1:])
assert shutil.disk_usage('/home/rehearsal').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
manifest = json.loads((evidence / 'input-archives.json').read_text(encoding='utf-8'))
assert hashlib.sha256((inputs / 'baseline.tar').read_bytes()).hexdigest() == manifest['baseline.tar']
selection = json.loads((evidence / 'selection.json').read_text(encoding='utf-8'))
for item in selection['patches']:
    assert hashlib.sha256((evidence / item['patch']).read_bytes()).hexdigest() == item['sha256']
PY
ip -brief link > "$evidence/build-network.txt"
go version > "$evidence/toolchain.txt"
gcc --version >> "$evidence/toolchain.txt"
go env GOOS GOARCH GOAMD64 CGO_ENABLED CC GOMODCACHE GOCACHE GOFLAGS GOTOOLCHAIN GOPROXY > "$evidence/build-environment.txt"
tar -xf "$inputs/baseline.tar" -C "$work/source"
cd "$work/source"
git apply --check "$extraction/01-node.patch" > "$evidence/node-apply.txt" 2>&1
git apply "$extraction/01-node.patch" >> "$evidence/node-apply.txt" 2>&1
python3 "$extraction/verify-tree.py" "$extraction" "$inputs" "$work/source" 1 > "$evidence/node-tree.txt"
sha256sum go.mod go.sum > "$evidence/modules-before.sha256"
date -u +%FT%TZ > "$evidence/build-started.txt"
set +e
timeout --signal=TERM --kill-after=20s 12m go build -p=2 -trimpath -buildvcs=false -o "$work/bin/efsn" ./cmd/efsn > "$evidence/build-node.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/build-node-exit.txt"
date -u +%FT%TZ > "$evidence/build-finished.txt"
python3 "$extraction/verify-tree.py" "$extraction" "$inputs" "$work/source" 1 > "$evidence/node-tree-after.txt"
sha256sum go.mod go.sum > "$evidence/modules-after.sha256"
cmp "$evidence/modules-before.sha256" "$evidence/modules-after.sha256"
df -B1 --output=source,size,used,avail / /mnt/d > "$evidence/capacity-after.txt"
du -sB1 "$work" > "$evidence/work-size.txt"
if [ "$code" = 0 ]; then
    sha256sum "$work/bin/efsn" > "$evidence/binary.sha256"
    go version -m "$work/bin/efsn" > "$evidence/build-info.txt"
fi
tail -n 20 "$evidence/build-node.txt"
exit "$code"
