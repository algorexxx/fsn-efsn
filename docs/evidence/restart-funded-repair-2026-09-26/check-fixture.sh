#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-funded-repair-2026-09-26"
binary="$workspace/tmp/funded-repair-diagnostic-tests"
[[ ! -e "$results/fixture-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$2" -test.run="^TestRestartNodeRehearsal$/dense_miner_fixture$" -test.v -test.timeout=2m' bash "$workspace" "$binary" > "$results/fixture-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/fixture-exit.txt"
tail -n 6 "$results/fixture-race.txt"
exit "$status"
