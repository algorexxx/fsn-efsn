#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-continuous-partitions-2026-09-26"
[[ ! -e "$results/regression-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; /usr/sbin/ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$1/tmp/continuous-partition-strict-tests" "-test.run=^TestRestartNodeRehearsal$/(dense_miner_fixture|heavier_stored_fork_peer)$" -test.v -test.timeout=4m' bash "$workspace" > "$results/regression-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/regression-exit.txt"
tail -n 8 "$results/regression-race.txt"
exit "$status"
