#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-small-reserve-2026-09-26"
binary="$workspace/tmp/small-reserve-final-tests"
command="$workspace/tmp/purchase-record-efsn"
cd "$workspace"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go build -race -p=2 -mod=readonly -o "$command" ./cmd/efsn > "$results/record-build.txt" 2>&1
sha256sum "$command" > "$results/record-binary.sha256"
[[ ! -e "$results/record-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_EFSN_COMMAND="$3" "$2" -test.run=^TestRestartPurchaseRecordCommand$ -test.v -test.timeout=2m' bash "$workspace" "$binary" "$command" > "$results/record-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/record-exit.txt"
tail -n 8 "$results/record-race.txt"
exit "$status"
