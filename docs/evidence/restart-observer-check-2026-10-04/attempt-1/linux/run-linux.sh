#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-check-2026-10-04"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
cp "$evidence/run-linux.sh" "$results/run-linux.sh"
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
runuser -u rehearsal -- env PATH="$PATH" go build -mod=readonly -o /tmp/fsn-observe-check ./cmd/fsn-observe > "$results/build.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/build-exit.txt"
[[ "$result" == 0 ]]
sha256sum /tmp/fsn-observe-check > "$results/binary.sha256"
set +e
runuser -u rehearsal -- env PATH="$PATH" FUSION_OBSERVER_CHECK_BINARY=/tmp/fsn-observe-check FUSION_HISTORY_CHECK_EVIDENCE="$results" go test -count=1 -race -p=2 -mod=readonly -v -timeout=3m ./internal/observe ./cmd/fsn-observe > "$results/tests-race.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
tail -n 8 "$results/tests-race.txt"
[[ "$result" == 0 ]]
