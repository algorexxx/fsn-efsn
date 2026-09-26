#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-full-state-partition-2026-09-26"
binary="$workspace/tmp/full-state-partition-diagnostic-tests"
cd "$workspace"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
[[ ! -e "$results/diagnostic-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/diagnostic-build.txt" 2>&1
sha256sum "$binary" > "$results/diagnostic-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_PARTITION_DIAGNOSIS="$1/tmp/full-state-partition-2026-09-26" "$2" -test.run="^TestFullStatePartitionColdDiagnosis$" -test.v -test.timeout=4m' bash "$workspace" "$binary" > "$results/diagnostic-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/diagnostic-exit.txt"
tail -n 10 "$results/diagnostic-race.txt"
exit "$status"
