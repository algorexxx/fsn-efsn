#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/manual-purchase-protocol-2026-09-27-attempt-02
results="$workspace/docs/evidence/restart-manual-purchase-delivery-2026-09-27"
binary="$root/protocol-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace/eth"
[[ ! -e "$binary" && ! -e "$results/protocol-race.txt" ]]
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
sha256sum restart_purchase_retry_test.go restart_manual_purchase_retry_test.go > "$results/protocol-sources.sha256"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off go list -f '{{join .GoFiles " "}}' . > "$results/production-files.txt"
read -r -a sources < "$results/production-files.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o "$binary" "${sources[@]}" restart_purchase_retry_test.go restart_manual_purchase_retry_test.go > "$results/protocol-build.txt" 2>&1
sha256sum "$binary" > "$results/protocol-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_MANUAL_RETRY="$1" "$2" -test.run="^TestRestartManualPurchasePeerRetry$" -test.v -test.timeout=3m' bash "$root" "$binary" > "$results/protocol-race.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$results/protocol-exit.txt"
tail -n 18 "$results/protocol-race.txt"
exit "$status"
