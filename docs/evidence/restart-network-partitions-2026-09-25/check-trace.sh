#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -overlay "$results/trace-overlay.json" -c -o "$workspace/tmp/network-partition-trace-tests" ./tests/restart > "$results/trace-build.txt" 2>&1
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief address; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NETWORK_PARTITION=1 "$1/tmp/network-partition-trace-tests" "-test.run=^TestRestartNetworkPartitionRehearsal$/fresh_dns_contact_udp_blocked$" -test.v -test.timeout=3m' bash "$workspace" > "$results/trace-live-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/trace-live-exit.txt"
tail -n 12 "$results/trace-live-race.txt"
exit "$status"
