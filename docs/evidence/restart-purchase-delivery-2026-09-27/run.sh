#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-purchase-delivery-2026-09-27"
binary="$workspace/tmp/purchase-delivery-2026-09-27/tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/historical-race.txt" && ! -e "$results/live-race.txt" ]]
mkdir -p "$(dirname "$binary")"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
sha256sum "$binary" > "$results/binary.sha256"
for stage in historical live; do
    testname=TestFullStateDeliveryHistoricalAdmission
    if [[ "$stage" == live ]]; then testname=TestFullStatePurchaseDirectDelivery; fi
    set +e
    unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_PURCHASE_DELIVERY="$1/tmp/full-state-purchase-delivery-2026-09-27" "$2" -test.run="^$3$" -test.v -test.timeout=7m' bash "$workspace" "$binary" "$testname" > "$results/$stage-race.txt" 2>&1
    status=$?
    set -e
    printf '%s\n' "$status" > "$results/$stage-exit.txt"
    tail -n 12 "$results/$stage-race.txt"
    if [[ "$status" != 0 ]]; then exit "$status"; fi
done
