#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-open-replay-2026-10-03"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp
export FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE= FUSION_BACKFILL_EVIDENCE= FUSION_TICKET_EVIDENCE= FUSION_HISTORY_COST_EVIDENCE=
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go tests/restart/*_test.go go.mod go.sum > "$results/sources.sha256"
set +e
runuser -u rehearsal -- env PATH="$PATH" go test -count=1 -race -p=2 -mod=readonly -v -timeout=3m ./internal/observe ./cmd/fsn-observe > "$results/tests-race.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
[[ "$result" == 0 ]]
build="/tmp/fusion-observer-open-replay-tests-$attempt"
mkdir "$build"
chown rehearsal "$build"
runuser -u rehearsal -- env PATH="$PATH" go test -race -p=2 -mod=readonly -c -o "$build/services-tests" ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" go build -race -mod=readonly -o "$build/fsn-observe" ./cmd/fsn-observe > "$results/build-observer.txt" 2>&1
sha256sum "$build/services-tests" "$build/fsn-observe" > "$results/binaries.sha256"
cd tests/restart
set +e
env TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_OBSERVER_BIN="$build/fsn-observe" FUSION_RESTART_OBSERVER_WORKLOAD_RESULTS="$results/workload" "$build/services-tests" -test.run='^TestObserverMixedWorkloadBudget$' -test.v -test.timeout=9m > "$results/workload-race.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/workload-exit.txt"
tail -n 10 "$results/workload-race.txt"
[[ "$result" == 0 ]]
