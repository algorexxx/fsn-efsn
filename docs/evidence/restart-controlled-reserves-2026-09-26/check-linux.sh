#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-controlled-reserves-2026-09-26"
binary="$workspace/tmp/controlled-reserve-tests"
cd "$workspace"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
mode=${1:?build or run}
if [[ "$mode" == build ]]; then
  {
    date -u --iso-8601=seconds
    git -c safe.directory="$workspace" rev-parse HEAD
    uname -a
    go version
    df -h /tmp
  } > "$results/environment.txt"
  runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/build.txt" 2>&1
  sha256sum "$binary" > "$results/binary.sha256"
  exit
fi
[[ "$mode" == run ]]
label=${2:?unique evidence label}
[[ "$label" =~ ^[a-z0-9-]+$ ]]
[[ ! -e "$results/$label-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 "$2" -test.run="^TestRestartNodeRehearsal$/(controlled_zero_ticket_reserves|dense_miner_fixture)$" -test.v -test.timeout=10m' bash "$workspace" "$binary" > "$results/$label-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/$label-exit.txt"
tail -n 10 "$results/$label-race.txt"
exit "$status"
