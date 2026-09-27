#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-autobuy-rebroadcast-2026-09-27"
binary="$workspace/tmp/autobuy-rebroadcast-2026-09-27/restart-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
date --utc --iso-8601=seconds
[[ ! -e "$results/focused-final.txt" && ! -e "$binary" ]]
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -v ./internal/ethapi > "$results/focused-final.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/focused-final-exit.txt"
tail -n 18 "$results/focused-final.txt"
[[ "$status" == 0 ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go build -p=2 -mod=readonly ./cmd/efsn ./les > "$results/node-build.txt" 2>&1
printf '0\n' > "$results/node-build-exit.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/restart-build.txt" 2>&1
sha256sum "$binary" > "$results/restart-binary.sha256"
set +e
unshare --net -- env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= "$binary" -test.run='^(TestAutoBuyRuntime|TestAutomaticPurchaseRecovery|TestAutomaticPurchaseStorageErrors|TestSubmittedTicketReplacementAllowsExplicitRetry)$' -test.v -test.timeout=10m > "$results/regression-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/regression-exit.txt"
tail -n 20 "$results/regression-race.txt"
exit "$status"
