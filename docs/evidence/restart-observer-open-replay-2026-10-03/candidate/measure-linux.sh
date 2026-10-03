#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-open-replay-2026-10-03"
variant="${1:?baseline or candidate required}"
[[ "$variant" == baseline || "$variant" == candidate ]]
results="$evidence/$variant"
[[ ! -e "$results" ]]
mkdir "$results"
cp "$evidence/measure-linux.sh" "$results/measure-linux.sh"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go go.mod go.sum > "$results/sources.sha256"
cp internal/observe/history.go "$results/history.go.txt"
cp internal/observe/history_cost_test.go "$results/history_cost_test.go.txt"
build="/tmp/fusion-observer-open-replay-$variant"
mkdir "$build"
chown rehearsal "$build"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -mod=readonly -c -o "$build/observe-tests" ./internal/observe > "$results/build.txt" 2>&1
sha256sum "$build/observe-tests" > "$results/binary.sha256"
cd internal/observe
set +e
env GOMAXPROCS=2 TMPDIR=/tmp FUSION_HISTORY_COST_EVIDENCE="$results/cost.json" /usr/bin/time -v -o "$results/resources.txt" "$build/observe-tests" -test.run='^TestHistoryRetainedSnapshotCost$' -test.v -test.timeout=3m > "$results/cost-test.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
cat "$results/cost-test.txt"
[[ "$result" == 0 ]]
