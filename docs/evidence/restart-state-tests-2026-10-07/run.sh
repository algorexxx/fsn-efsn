#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-state-tests-2026-10-07"
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
phase="$1"
test "$phase" = api || test "$phase" = qualified || test "$phase" = verified
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache"
export GOTMPDIR=/home/rehearsal/results/restart-release-text-2026-10-04/tmp TMPDIR=/home/rehearsal/results/restart-release-text-2026-10-04/tmp
unset GODEBUG GOEXPERIMENT
python3 - <<'PY'
import shutil
assert shutil.disk_usage('/home/rehearsal/results').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
gofmt -w "$workspace/core/state/state_test.go" "$workspace/core/state/statedb_test.go" "$workspace/core/state/iterator_test.go" "$workspace/core/state/sync_test.go" "$workspace/core/state/suicide_test.go"
python3 "$evidence/prepare.py" "$phase"
date -u +%FT%TZ > "$evidence/$phase/started.txt"
ip -brief link > "$evidence/$phase/network.txt"
for stage in baseline candidate; do
    if [ "$stage" = baseline ]; then directory=restart-release-jwt-2026-10-04; else directory=restart-release-text-2026-10-04; fi
    cd "/home/rehearsal/results/$directory/node"
    set +e
    timeout --signal=TERM --kill-after=20s 7m go test -overlay="$evidence/$phase/$stage-overlay.json" -race -p=2 -count=1 -timeout=5m -v ./core/state > "$evidence/$phase/$stage.txt" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/$phase/$stage-exit.txt"
    printf '%s %s exit=%s\n' "$phase" "$stage" "$code"
done
date -u +%FT%TZ > "$evidence/$phase/finished.txt"
