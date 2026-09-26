#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-full-state-participant-2026-09-26"
binary="$workspace/tmp/full-state-participant-tests"
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
[[ ! -e "$results/participant-attempt-02-race.txt" ]]
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_PARTICIPANT="$1/tmp/full-state-participant-2026-09-26-attempt-02" "$2" -test.run="^TestFullStateParticipantEntry$" -test.v -test.timeout=10m' bash "$workspace" "$binary" > "$results/participant-attempt-02-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/participant-attempt-02-exit.txt"
tail -n 10 "$results/participant-attempt-02-race.txt"
exit "$status"
