#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace/tests/restart"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NETWORK_PARTITION=1 "$1/tmp/network-partition-trace-tests" "-test.run=^TestRestartNetworkPartitionRehearsal$/fresh_dns_contact_udp_blocked$" -test.count=3 -test.v -test.timeout=6m' bash "$workspace" > "$results/trace-repeat-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/trace-repeat-exit.txt"
tail -n 12 "$results/trace-repeat-race.txt"
exit "$status"
