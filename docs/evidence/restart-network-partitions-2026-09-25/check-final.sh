#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$workspace/tmp/network-partition-final-tests" ./tests/restart > "$results/final-build.txt" 2>&1
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief address; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NETWORK_PARTITION=1 "$1/tmp/network-partition-final-tests" -test.run=^TestRestartNetworkPartitionRehearsal$ -test.v -test.timeout=8m' bash "$workspace" > "$results/final-live-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/final-live-exit.txt"
tail -n 35 "$results/final-live-race.txt"
exit "$status"
