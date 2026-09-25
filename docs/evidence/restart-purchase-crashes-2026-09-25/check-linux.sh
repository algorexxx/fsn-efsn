#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-purchase-crashes-2026-09-25"
binary="$workspace/tmp/purchase-crash-linux-tests"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" FUSION_RESTART_CHAINDATA= FUSION_PURCHASE_CRASH_REHEARSAL=1 "$binary" '-test.run=^TestAutomaticPurchaseCrashBoundaries$' -test.v -test.timeout=10m > "$results/linux-crashes-race.txt" 2>&1
tail -n 19 "$results/linux-crashes-race.txt"
