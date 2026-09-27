#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
root=/mnt/d/FusionRehearsal/peer-purchase-retry-2026-09-27
results="$workspace/docs/evidence/restart-manual-purchase-delivery-2026-09-27"
binary=/mnt/d/FusionRehearsal/manual-purchase-protocol-2026-09-27-attempt-02/protocol-tests
cd "$workspace/eth"
[[ ! -e "$results/regression-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_PEER_RETRY="$1" "$2" -test.run="^TestRestartPeerPurchaseRetry$" -test.v -test.timeout=3m' bash "$root" "$binary" > "$results/regression-race.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$results/regression-exit.txt"
tail -n 18 "$results/regression-race.txt"
exit "$status"
