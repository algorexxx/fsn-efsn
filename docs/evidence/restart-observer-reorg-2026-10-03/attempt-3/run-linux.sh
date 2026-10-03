#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-reorg-2026-10-03"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt"
[[ ! -e "$results" ]]
mkdir "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go tests/restart/*_test.go go.mod go.sum > "$results/sources.sha256"
build="/tmp/fusion-observer-reorg-$attempt"
test ! -e "$build"
mkdir "$build"
chown rehearsal "$build"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o "$build/services-tests" ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build -race -mod=readonly -o "$build/fsn-observe" ./cmd/fsn-observe > "$results/build-observer.txt" 2>&1
sha256sum "$build/services-tests" "$build/fsn-observe" > "$results/binaries.sha256"
cd tests/restart
for mode in reorg ordinary; do
    test_name=TestObserverCompetingReorganization
    if [[ "$mode" == ordinary ]]; then test_name=TestObserverOrdinaryMining; fi
    date -u +%FT%TZ > "$results/$mode-started.txt"
    set +e
    env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_OBSERVER_BIN="$build/fsn-observe" FUSION_RESTART_OBSERVER_REORG_RESULTS="$results/reorg" FUSION_RESTART_OBSERVER_MINING_RESULTS="$results/ordinary" "$build/services-tests" -test.run="^$test_name\$" -test.v -test.timeout=9m > "$results/$mode-race.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/$mode-exit.txt"
    date -u +%FT%TZ > "$results/$mode-finished.txt"
    tail -n 12 "$results/$mode-race.txt"
    [[ "$result" == 0 ]]
done
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
