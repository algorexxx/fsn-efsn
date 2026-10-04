#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-text-2026-10-04
work=/home/rehearsal/results/restart-release-text-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOMAXPROCS=2
export GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
test ! -e "$evidence/resolve-ready-exit.txt"
cd "$work/node"
set +e
timeout --signal=TERM --kill-after=10s 3m go get golang.org/x/text@v0.39.0 > "$evidence/resolve-ready.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/resolve-ready-exit.txt"
cat "$evidence/resolve-ready.txt"
exit "$code"
