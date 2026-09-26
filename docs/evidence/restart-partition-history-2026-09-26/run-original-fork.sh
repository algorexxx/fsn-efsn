#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-partition-history-2026-09-26"
binary="$workspace/tmp/partition-history-2026-09-26/tests-original-fork"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$results/original-fork-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/original-fork-build.txt" 2>&1
sha256sum "$binary" > "$results/original-fork-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; cd "$1/tests/restart"; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_HISTORY_INPUT="$1/tmp/partition-history-2026-09-26/history.rlp" FUSION_RESTART_HISTORY_RECHECK="$1/tmp/full-state-partition-2026-09-26" "$2" -test.run="^TestFullStateOriginalForkHistory$" -test.v -test.timeout=5m' bash "$workspace" "$binary" > "$results/original-fork-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/original-fork-exit.txt"
tail -n 10 "$results/original-fork-race.txt"
exit "$status"
