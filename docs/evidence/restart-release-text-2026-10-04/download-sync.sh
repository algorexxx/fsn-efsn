#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-text-2026-10-04
work=/home/rehearsal/results/restart-release-text-2026-10-04
export PATH=/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin:/usr/bin:/bin
export GOTOOLCHAIN=local GOWORK=off GO111MODULE=on GOFLAGS= GOMAXPROCS=2
export GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
test ! -e "$evidence/sync-download.json"
cd "$work/download"
timeout --signal=TERM --kill-after=10s 3m go mod download -json golang.org/x/sync@v0.21.0 > "$evidence/sync-download.json" 2> "$evidence/sync-download.stderr.txt"
