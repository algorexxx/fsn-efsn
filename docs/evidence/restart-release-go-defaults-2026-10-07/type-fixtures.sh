#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-go-defaults-2026-10-07"
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache"
export GOTMPDIR=/home/rehearsal/results/restart-release-text-2026-10-04/tmp TMPDIR=/home/rehearsal/results/restart-release-text-2026-10-04/tmp
unset GODEBUG GOEXPERIMENT
test ! -e "$evidence/type-fixtures-started.txt"
date -u +%FT%TZ > "$evidence/type-fixtures-started.txt"
python3 "$evidence/type-fixtures.py"
for stage in baseline candidate; do
    if [ "$stage" = baseline ]; then directory=restart-release-jwt-2026-10-04; else directory=restart-release-text-2026-10-04; fi
    cd "/home/rehearsal/results/$directory/node"
    set +e
    timeout --signal=TERM --kill-after=20s 7m go test -overlay="$evidence/$stage-type-overlay.json" -race -p=2 -count=1 -timeout=5m -v ./core/types > "$evidence/$stage-core-types-repaired.txt" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/$stage-core-types-repaired-exit.txt"
    printf '%s exit=%s\n' "$stage" "$code"
done
date -u +%FT%TZ > "$evidence/type-fixtures-finished.txt"
