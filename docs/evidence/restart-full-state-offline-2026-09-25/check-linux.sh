#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-full-state-offline-2026-09-25"
binary="$workspace/tmp/full-state-offline-linux-tests"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= "$binary" '-test.run=^TestOfflineRecovery(ProcessCuts|UncertainCuts|Refusals)$' -test.v -test.timeout=3m > "$results/linux-regression-race.txt" 2>&1
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= FUSION_RESTART_OFFLINE_FULL_STATE_ROOT="$workspace/tmp/full-state-offline-linux-2026-09-25" "$binary" '-test.run=^TestFullStateOfflineRecovery$' -test.v -test.timeout=15m > "$results/linux-full-state-race.txt" 2>&1
tail -n 12 "$results/linux-full-state-race.txt"
