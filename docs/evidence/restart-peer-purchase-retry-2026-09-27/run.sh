#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-peer-purchase-retry-2026-09-27"
binary="$workspace/tmp/peer-purchase-retry-2026-09-27/protocol-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace/eth"
[[ ! -e "$binary" && ! -e "$results/protocol-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off go list -f '{{join .GoFiles " "}}' . > "$results/production-files.txt"
read -r -a sources < "$results/production-files.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" "${sources[@]}" restart_purchase_retry_test.go > "$results/build.txt" 2>&1
sha256sum "$binary" > "$results/binary.sha256"
set +e
unshare --net -- env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_PEER_RETRY="$workspace/tmp/peer-purchase-retry-2026-09-27" "$binary" -test.run='^TestRestartPeerPurchaseRetry$' -test.v -test.timeout=3m > "$results/protocol-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/protocol-exit.txt"
tail -n 22 "$results/protocol-race.txt"
exit "$status"
