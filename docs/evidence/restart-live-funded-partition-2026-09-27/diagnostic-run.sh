#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/live-funded-partition-2026-09-27-admission
results="$workspace/docs/evidence/restart-live-funded-partition-2026-09-27"
binary="$root/restart-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/admission-race.txt" ]]
sha256sum tests/restart/{full_state_manual_admission_linux,full_state_delivery_linux}_test.go > "$results/admission-sources.sha256"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/admission-build.txt" 2>&1
sha256sum "$binary" > "$results/admission-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_HOST_STORAGE=/mnt/d FUSION_RESTART_PURCHASE_DELIVERY="$2" "$3" -test.run="^TestFullStateManualGapHistoricalAdmission$" -test.v -test.timeout=3m' bash "$workspace" "$root" "$binary" > "$results/admission-race.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$results/admission-exit.txt"
tail -n 15 "$results/admission-race.txt"
exit "$status"
