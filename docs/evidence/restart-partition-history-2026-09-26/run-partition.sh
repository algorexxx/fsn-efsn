#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-partition-history-2026-09-26"
binary="$workspace/tmp/partition-history-2026-09-26/tests"
[[ ! -e "$results/partition-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_HISTORY_INPUT="$1/tmp/partition-history-2026-09-26/history.rlp" FUSION_RESTART_FULL_STATE_PARTITION="$1/tmp/full-state-history-partition-2026-09-26" "$2" -test.run="^TestFullStatePartitionRepair$" -test.v -test.timeout=15m' bash "$workspace" "$binary" > "$results/partition-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/partition-exit.txt"
tail -n 10 "$results/partition-race.txt"
exit "$status"
