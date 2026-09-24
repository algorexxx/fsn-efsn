#!/bin/bash
set -euo pipefail
source=/home/rehearsal/fsn-efsn-crash-rehearsal
results=/home/rehearsal/results/restart-crash-rehearsal-2026-09-24
test -x "$results/crash-tests"
test ! -e "$results/full-race.txt"
cd "$source"
export PATH=/opt/fusion-toolchain/go/bin:$PATH
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go build -p=2 -mod=readonly -o "$results/efsn" ./cmd/efsn > "$results/build-node.txt" 2>&1
{
    date -u +%FT%TZ
    go version
    gcc --version | head -n 1
    sha256sum "$results/crash-tests" "$results/efsn"
    sha256sum core/blockchain.go tests/restart/crash_test.go
} > "$results/identity.txt"
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env FUSION_RESTART_CRASH_REHEARSAL=1 FUSION_RESTART_NODE_REHEARSAL=1 GOMAXPROCS=2 "$1" -test.v -test.timeout=10m' bash "$results/crash-tests" > "$results/full-race.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/full-exit-code.txt"
if [ "$code" -eq 0 ]; then
    unshare --net -- runuser -u rehearsal -- env FUSION_RESTART_CRASH_REHEARSAL=1 GOMAXPROCS=2 "$results/crash-tests" '-test.run=^TestRestartCrashBoundaries$' -test.v -test.count=2 -test.timeout=6m > "$results/crash-race-2.txt" 2>&1
    code=$?
    printf '%s\n' "$code" > "$results/crash-exit-code.txt"
fi
date -u +%FT%TZ > "$results/finished.txt"
tail -n 8 "$results/full-race.txt"
exit "$code"
