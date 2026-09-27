#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-existing-funds-2026-09-27"
binary="$workspace/tmp/existing-funds-2026-09-27/tests"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
case "${1:?build or run}" in
build)
  [[ ! -e "$binary" && ! -e "$results/build.txt" ]]
  mkdir -p "$(dirname "$binary")"
  { date -u --iso-8601=seconds; git -c safe.directory="$workspace" rev-parse HEAD; go version; uname -a; df -B1 / /mnt/c /mnt/d; } > "$results/environment.txt"
  runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
  sha256sum "$binary" > "$results/binary.sha256"
  ;;
run)
  [[ ! -e "$results/recovery-race.txt" ]]
  set +e
  unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_HOST_STORAGE=/mnt/c FUSION_RESTART_FUNDING_RECOVERY="$1/tmp/full-state-existing-funds-2026-09-27" "$2" -test.run="^TestFullStateFundingRecovery$" -test.v -test.timeout=5m' bash "$workspace" "$binary" > "$results/recovery-race.txt" 2>&1
  status=$?
  set -e
  printf '%s\n' "$status" > "$results/recovery-exit.txt"
  tail -n 12 "$results/recovery-race.txt"
  exit "$status"
  ;;
*) exit 2 ;;
esac
