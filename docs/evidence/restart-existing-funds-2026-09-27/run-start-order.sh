#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-existing-funds-2026-09-27"
binary="$workspace/tmp/existing-funds-2026-09-27/tests-start-order"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$binary" && ! -e "$results/start-order-race.txt" ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/start-order-build.txt" 2>&1
sha256sum "$binary" > "$results/start-order-binary.sha256"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_NODE_DEBUG=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_FUNDING_LIVE="$1/tmp/full-state-existing-funds-2026-09-27" "$2" -test.run="^TestFullStateFundingStartOrder$" -test.v -test.timeout=7m' bash "$workspace" "$binary" > "$results/start-order-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/start-order-exit.txt"
tail -n 12 "$results/start-order-race.txt"
exit "$status"
