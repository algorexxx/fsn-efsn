#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-history-cost-2026-10-03"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off GOMAXPROCS=2 CGO_ENABLED=1 GOTMPDIR=/tmp
export FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE= FUSION_BACKFILL_EVIDENCE= FUSION_TICKET_EVIDENCE= FUSION_HISTORY_COST_EVIDENCE=
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go go.mod go.sum > "$results/sources.sha256"
sha256sum docs/evidence/restart-observer-services-2026-09-27/attempt-4/services/ipc-converged*.json > "$results/fixture.sha256"
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-before.txt"
set +e
runuser -u rehearsal -- env PATH="$PATH" go test -count=1 -race -p=2 -mod=readonly -v -timeout=3m ./internal/observe ./cmd/fsn-observe > "$results/tests-race.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/tests-exit.txt"
[[ "$result" == 0 ]]
build="/tmp/fusion-history-cost-$attempt"
mkdir "$build"
chown rehearsal "$build"
runuser -u rehearsal -- env PATH="$PATH" go test -mod=readonly -c -o "$build/observe-tests" ./internal/observe > "$results/build.txt" 2>&1
sha256sum "$build/observe-tests" > "$results/binary.sha256"
cd internal/observe
set +e
env FUSION_HISTORY_COST_EVIDENCE="$results/cost.json" /usr/bin/time -v -o "$results/resources.txt" "$build/observe-tests" -test.run='^TestHistoryRetainedSnapshotCost$' -test.v -test.timeout=3m > "$results/cost-test.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/cost-exit.txt"
[[ "$result" == 0 ]]
df -B1 /tmp /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 6 "$results/tests-race.txt"
cat "$results/cost-test.txt"
