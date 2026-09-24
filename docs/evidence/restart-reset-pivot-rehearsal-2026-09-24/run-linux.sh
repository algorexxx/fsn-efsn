#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-reset-pivot-rehearsal
results=/home/rehearsal/results/restart-reset-pivot-rehearsal-2026-09-24
test ! -e "$source"
test ! -e "$results"
mkdir "$source" "$results"
tar -xf "$workspace/tmp/restart-reset-pivot-base.tar" -C "$source"
for path in tests/restart/crash_test.go tests/restart/reset_pivot_test.go tests/restart/anchor_enforcement_test.go; do
    cp "$workspace/$path" "$source/$path"
done
chown -R rehearsal:rehearsal "$source" "$results"
cd "$source"
export PATH=/opt/fusion-toolchain/go/bin:$PATH
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$results/reset-pivot-tests" ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go build -p=2 -mod=readonly -o "$results/efsn" ./cmd/efsn > "$results/build-node.txt" 2>&1
{
    date -u +%FT%TZ
    go version
    gcc --version | head -n 1
    sha256sum "$workspace/tmp/restart-reset-pivot-base.tar" "$results/reset-pivot-tests" "$results/efsn"
    sha256sum core/blockchain.go core/headerchain.go tests/restart/crash_test.go tests/restart/reset_pivot_test.go tests/restart/anchor_enforcement_test.go
} > "$results/identity.txt"
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env FUSION_RESTART_CRASH_REHEARSAL=1 FUSION_RESTART_NODE_REHEARSAL=1 GOMAXPROCS=2 "$1" -test.v -test.timeout=12m' bash "$results/reset-pivot-tests" > "$results/full-race.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/full-exit-code.txt"
if [ "$code" -eq 0 ]; then
    unshare --net -- runuser -u rehearsal -- env FUSION_RESTART_CRASH_REHEARSAL=1 GOMAXPROCS=2 "$results/reset-pivot-tests" '-test.run=^TestRestartCrashBoundaries$/(reset|pivot)' -test.v -test.count=2 -test.timeout=6m > "$results/reset-pivot-race-2.txt" 2>&1
    code=$?
    printf '%s\n' "$code" > "$results/reset-pivot-exit-code.txt"
fi
date -u +%FT%TZ > "$results/finished.txt"
tail -n 8 "$results/full-race.txt"
exit "$code"
