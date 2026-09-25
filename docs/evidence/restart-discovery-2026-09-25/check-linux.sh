#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-discovery-2026-09-25"
label=${1:-current}
case "$label" in baseline|current) ;; *) exit 2 ;; esac
binary="$workspace/tmp/discovery-$label-linux-tests"
build_options=()
if [ "$label" = baseline ]; then
    build_options+=("-overlay=$workspace/tmp/discovery-pre-p10-overlay/overlay.json")
fi
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly "${build_options[@]}" -c -o "$binary" ./tests/restart > "$results/$label-build.txt" 2>&1
cd tests/restart
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_DISCOVERY_REHEARSAL=1 "$1" "-test.run=^TestRestartDiscoveryRehearsal$" -test.v -test.timeout=4m' bash "$binary" > "$results/$label-race.txt" 2>&1
tail -n 14 "$results/$label-race.txt"
