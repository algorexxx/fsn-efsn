#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace"
mode=${1:?unit, broad, live-before, live-after, or partitions}
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
case "$mode" in
  unit) pattern='^TestRestartDiscoveryRejectsSelf$'; packages='./p2p/discover' ;;
  broad) pattern='.'; packages='./p2p/discover ./p2p ./cmd/utils' ;;
  live-*) pattern='^TestRestartDiscoverySelfLive$'; packages='./p2p/discover' ;;
  partitions) pattern='^TestRestartNetworkPartitionRehearsal$'; packages='./tests/restart' ;;
  *) exit 2 ;;
esac
overlay=
if [[ "$mode" == live-before ]]; then
  overlay="-overlay=$results/self-baseline-overlay.json"
fi
if [[ "$mode" == partitions ]]; then
  runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$workspace/tmp/network-partition-corrected-tests" ./tests/restart > "$results/corrected-build.txt" 2>&1
fi
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip address add 172.0.1.1/16 dev lo; ip address add 172.0.2.1/16 dev lo; ip address add 172.0.3.1/16 dev lo; if [[ "$4" == partitions ]]; then cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NETWORK_PARTITION=1 "$1/tmp/network-partition-corrected-tests" "-test.run=$2" -test.v -test.timeout=8m; fi; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 FUSION_RESTART_ADDRESS_REHEARSAL=1 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly ${3:+"$3"} -count=1 -v -run="$2" -timeout=4m $5' bash "$workspace" "$pattern" "$overlay" "$mode" "$packages" > "$results/corrected-$mode-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/corrected-$mode-exit.txt"
tail -n 20 "$results/corrected-$mode-race.txt"
exit "$status"
