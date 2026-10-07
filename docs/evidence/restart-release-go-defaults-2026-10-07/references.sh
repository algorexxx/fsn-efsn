#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-go-defaults-2026-10-07"
work=/home/rehearsal/results/restart-release-go-defaults-2026-10-07
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GO111MODULE=off
export GOMAXPROCS=2 GOCACHE="$selected/repeat-cache"
unset GOFLAGS GODEBUG GOEXPERIMENT
cd "$work"
timeout 2m go build -p=2 -o references "$evidence/references.go"
for name in efsn fsn-recovery; do
    test ! -e "$evidence/references-$name.json"
    timeout 1m ./references "$workspace/docs/evidence/restart-release-text-2026-10-04/dependencies-$name.txt" > "$evidence/references-$name.json"
done
