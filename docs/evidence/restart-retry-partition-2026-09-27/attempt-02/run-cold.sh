#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/retry-partition-2026-09-27-attempt-02
results="$workspace/docs/evidence/restart-retry-partition-2026-09-27/attempt-02"
binary="$root/restart-tests"
[[ -e "$results/live-exit.txt" && ! -e "$results/cold-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_RETRY_PARTITION="$2" "$3" -test.run="^TestFullStateRetainedPartitionColdAudit$" -test.v -test.timeout=4m' bash "$workspace" "$root" "$binary" > "$results/cold-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/cold-exit.txt"
tail -n 14 "$results/cold-race.txt"
exit "$status"
