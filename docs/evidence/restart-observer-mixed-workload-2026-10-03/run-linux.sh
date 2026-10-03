#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-mixed-workload-2026-10-03"
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
build="/tmp/fusion-observer-mixed-$attempt"
test ! -e "$build"
mkdir "$build"
chown rehearsal "$build"
for mode in plain race; do
    mkdir "$results/$mode"
    flags=()
    if [[ "$mode" == race ]]; then flags=(-race); fi
    runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test "${flags[@]}" -p=2 -mod=readonly -c -o "$build/$mode-tests" ./tests/restart > "$results/$mode/build-tests.txt" 2>&1
    runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build "${flags[@]}" -mod=readonly -o "$build/$mode-observer" ./cmd/fsn-observe > "$results/$mode/build-observer.txt" 2>&1
    sha256sum "$build/$mode-tests" "$build/$mode-observer" > "$results/$mode/binaries.sha256"
    date -u +%FT%TZ > "$results/$mode/started.txt"
    set +e
    (cd tests/restart && env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_OBSERVER_BIN="$build/$mode-observer" FUSION_RESTART_OBSERVER_WORKLOAD_RESULTS="$results/$mode/workload" /usr/bin/time -v -o "$results/$mode/resources.txt" "$build/$mode-tests" -test.run='^TestObserverMixedWorkloadBudget$' -test.v -test.timeout=9m) > "$results/$mode/tests.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/$mode/test-exit.txt"
    date -u +%FT%TZ > "$results/$mode/finished.txt"
    tail -n 10 "$results/$mode/tests.txt"
    [[ "$result" == 0 ]]
done
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
