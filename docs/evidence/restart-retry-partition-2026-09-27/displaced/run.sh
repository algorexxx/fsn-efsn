#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/retry-partition-2026-09-27-displaced
results="$workspace/docs/evidence/restart-retry-partition-2026-09-27/displaced"
binary="$root/restart-tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/race.txt" ]]
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
sha256sum "$binary" > "$results/binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_RETRY_PARTITION="$2" "$3" -test.run="^TestFullStateRetainedPartitionDisplacedAudit$" -test.v -test.timeout=4m' bash "$workspace" "$root" "$binary" > "$results/race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/exit.txt"
tail -n 16 "$results/race.txt"
exit "$status"
