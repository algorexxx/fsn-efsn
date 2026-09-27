#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-autobuy-rebroadcast-2026-09-27"
binary="$workspace/tmp/autobuy-rebroadcast-2026-09-27/restart-tests"
[[ ! -e "$results/live-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_PURCHASE_DELIVERY=/mnt/d/FusionRehearsal/autobuy-rebroadcast-2026-09-27 "$2" -test.run="^TestFullStatePurchaseAutomaticRebroadcast$" -test.v -test.timeout=7m' bash "$workspace" "$binary" > "$results/live-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/live-exit.txt"
tail -n 18 "$results/live-race.txt"
exit "$status"
