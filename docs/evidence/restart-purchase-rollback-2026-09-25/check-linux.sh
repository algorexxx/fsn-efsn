#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-purchase-rollback-2026-09-25"
binary="$workspace/tmp/purchase-rollback-linux-tests"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$1" "-test.run=^TestRestartNodeRehearsal$/purchase_peer_nonce_rollback$" -test.v -test.timeout=4m' bash "$binary" > "$results/linux-rollback-race.txt" 2>&1
tail -n 4 "$results/linux-rollback-race.txt"
