#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-go-defaults-2026-10-07"
work=/home/rehearsal/results/restart-release-go-defaults-2026-10-07
candidate=/home/rehearsal/results/restart-release-text-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$evidence/inspection-started.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache"
export GOTMPDIR="$candidate/tmp" TMPDIR="$candidate/tmp"
unset GODEBUG GOEXPERIMENT
python3 - <<'PY'
import shutil
assert shutil.disk_usage('/home/rehearsal/results').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
test ! -e "$work"
mkdir "$work"
date -u +%FT%TZ > "$evidence/inspection-started.txt"
ip -brief link > "$evidence/network.txt"
free -b > "$evidence/memory-before.txt"
df -B1 / /mnt/d > "$evidence/disk-before.txt"
go version > "$evidence/compiler.txt"
cp "$selected/toolchain/go/src/internal/godebugs/table.go" "$evidence/compiler-godebugs.go.txt"
cp "$selected/toolchain/go/doc/godebug.md" "$evidence/compiler-godebug.md"
cp "$selected/toolchain/go/LICENSE" "$evidence/compiler-LICENSE"
python3 "$workspace/docs/evidence/restart-release-text-2026-10-04/report.py" --check > "$evidence/prior-input-verification.txt"
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=node; else folder=recovery; fi
    cd "$candidate/$folder"
    set +e
    timeout --signal=TERM --kill-after=20s 10m go build -p=2 -trimpath -buildvcs=false \
        '-gcflags=github.com/FusionFoundation/efsn/v5/...=-d=loopvar=2' \
        -o "$work/$name-diagnostic" "./cmd/$name" > "$evidence/loops-$name.txt" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/loops-$name-exit.txt"
    printf '%s exit=%s\n' "$name" "$code"
    test "$code" = 0
done
free -b > "$evidence/memory-after.txt"
df -B1 / /mnt/d > "$evidence/disk-after.txt"
du -s -B1 "$work" > "$evidence/allocation.txt"
date -u +%FT%TZ > "$evidence/inspection-finished.txt"
