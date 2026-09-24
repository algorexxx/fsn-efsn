#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/recovery-guard-linux-v4-src"
results="$workspace/docs/evidence/restart-recovery-guard-2026-09-24"
binary="$workspace/tmp/recovery-guard-linux-v4-tests"
if [[ "${1:-}" == legacy ]]; then
    ip link set lo up
    cd "$source/tests/restart"
    exec runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_NODE_REHEARSAL=1 "$binary" '-test.run=^TestRestartNodeRehearsal$' -test.v -test.timeout=5m
fi
if [[ "${1:-}" == nodes ]]; then
    ip link set lo up
    cd "$source/tests/restart"
    exec runuser -u rehearsal -- env GOMAXPROCS=2 FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NODE_COPIES="$workspace/tmp/recovery-node-v4" "$binary" '-test.run=^TestFullStateRecoveryNodes$' -test.v -test.timeout=5m
fi
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/recovery-guard-base.tar" -C "$source"
cp -r "$workspace/internal/recovery" "$source/internal/"
cp -r "$workspace/cmd/fsn-recovery" "$source/cmd/"
cp "$workspace"/tests/restart/recovery*_test.go "$workspace/tests/restart/node_rehearsal_linux_test.go" "$workspace/tests/restart/full_state_handover_ledger_test.go" "$source/tests/restart/"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-v4-build.txt" 2>&1
sha256sum "$binary" tests/restart/recovery*_test.go tests/restart/node_rehearsal_linux_test.go tests/restart/full_state_handover_ledger_test.go > "$results/linux-v4-identities.txt"
unshare --net -- bash "$results/check-linux-v4.sh" nodes > "$results/linux-v4-two-nodes-race.txt" 2>&1
tail -n 8 "$results/linux-v4-two-nodes-race.txt"
