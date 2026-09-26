#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace"
set +e
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly ./p2p/discover -run '^TestRestartDiscoveryRejectsSelf$' -v -count=1 > "$results/self-baseline-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/self-baseline-exit.txt"
cat "$results/self-baseline-race.txt"
exit "$status"
