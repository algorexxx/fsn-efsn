#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-peer-purchase-retry-2026-09-27"
cd "$workspace"
[[ ! -e "$results/package-build.txt" ]]
set +e
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -run='^$' ./eth > "$results/package-build.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/package-build-exit.txt"
cat "$results/package-build.txt"
exit "$status"
