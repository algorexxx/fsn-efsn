#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-backlog-2026-10-04"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
cp "$workspace/internal/observe/history_backlog_test.go" "$results/history_backlog_test.go.txt"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp
export FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE= FUSION_BACKFILL_EVIDENCE= FUSION_TICKET_EVIDENCE= FUSION_HISTORY_COST_EVIDENCE= FUSION_HISTORY_BACKLOG_EVIDENCE=
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
df -B1 /tmp "$workspace" > "$results/capacity.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go go.mod go.sum > "$results/sources.sha256"
set +e
runuser -u rehearsal -- env PATH="$PATH" go test -count=1 -race -p=2 -mod=readonly -v -timeout=3m ./internal/observe ./cmd/fsn-observe > "$results/tests-race.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
[[ "$result" == 0 ]]
for mode in ordinary race; do
    options=()
    if [[ "$mode" == race ]]; then options=(-race); fi
    set +e
    runuser -u rehearsal -- env PATH="$PATH" FUSION_HISTORY_BACKLOG_EVIDENCE="$results/backlog-$mode.json" go test "${options[@]}" -count=1 -p=2 -mod=readonly -run '^TestHistoryBoundedBacklogAndClosedCopy$' -v -timeout=8m ./internal/observe > "$results/backlog-$mode.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/backlog-$mode-exit.txt"
    tail -n 5 "$results/backlog-$mode.txt"
    [[ "$result" == 0 ]]
done
