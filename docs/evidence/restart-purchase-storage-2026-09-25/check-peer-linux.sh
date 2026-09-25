#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-purchase-storage-2026-09-25"
binary="$workspace/tmp/purchase-peer-linux-tests"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-peer-build.txt" 2>&1
cd tests/restart
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$1" "-test.run=^TestRestartNodeRehearsal$/purchase_peer" -test.v -test.timeout=6m' bash "$binary" "$temporary" > "$results/linux-peer-final-race.txt" 2>&1
tail -n 5 "$results/linux-peer-final-race.txt"
