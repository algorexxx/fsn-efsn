#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-parent-isolation-2026-09-25"
binary="$workspace/tmp/parent-isolation-linux-tests"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= "$binary" '-test.run=^Test(FinalizeParentIsolatedFromConcurrentImport|HeaderBatchUsesUnstoredParents)$' -test.v -test.count=5 -test.timeout=2m > "$results/linux-parent-race.txt" 2>&1
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= "$binary" '-test.run=^TestRestartAnchorEntryPointsCharacterization$' -test.v -test.timeout=3m > "$results/linux-anchor-race.txt" 2>&1
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$1" "-test.run=^TestRestartNodeRehearsal$/(readiness_mining_crash|compatible_peer|heavier_stored_fork_peer|incompatible_database_startup|purchase_peer_nonce_rollback)$" -test.v -test.timeout=6m' bash "$binary" > "$results/linux-node-regressions-race.txt" 2>&1
tail -n 4 "$results/linux-parent-race.txt"
tail -n 7 "$results/linux-node-regressions-race.txt"
