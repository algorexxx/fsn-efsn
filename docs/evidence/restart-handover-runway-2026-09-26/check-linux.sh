#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-handover-runway-2026-09-26"
binary="$workspace/tmp/handover-runway-final-tests"
cd "$workspace"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
{
  date -u --iso-8601=seconds
  git -c safe.directory="$workspace" rev-parse HEAD
  uname -a
  go version
} > "$results/final-environment.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/final-build.txt" 2>&1
sha256sum "$binary" > "$results/final-binary.sha256"
[[ ! -e "$results/final-race.txt" ]]
set +e
unshare --net -- runuser -u rehearsal -- bash -c 'cd "$1/tests/restart"; exec env GOMAXPROCS=2 TMPDIR=/tmp "$2" -test.run="^TestPreservedHandoverFundingCoverage$" -test.v -test.timeout=2m' bash "$workspace" "$binary" > "$results/final-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/final-exit.txt"
tail -n 8 "$results/final-race.txt"
exit "$status"
