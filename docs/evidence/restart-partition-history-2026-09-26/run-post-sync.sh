#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-partition-history-2026-09-26"
binary="$workspace/tmp/partition-history-2026-09-26/tests-post-sync"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$results/post-sync-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/post-sync-build.txt" 2>&1
sha256sum "$binary" > "$results/post-sync-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; cd "$1/tests/restart"; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_POST_SYNC="$1/tmp/full-state-history-partition-2026-09-26" "$2" -test.run="^TestFullStatePostSyncAccounting$" -test.v -test.timeout=4m' bash "$workspace" "$binary" > "$results/post-sync-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/post-sync-exit.txt"
tail -n 12 "$results/post-sync-race.txt"
exit "$status"
