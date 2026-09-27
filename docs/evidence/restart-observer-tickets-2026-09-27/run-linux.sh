#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-tickets-2026-09-27"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go > "$results/sources.sha256"
mkdir -p tmp/restart-observer-tickets
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE= FUSION_BACKFILL_EVIDENCE= FUSION_TICKET_EVIDENCE="$results" go test -count=1 -race -p=2 -mod=readonly -v -timeout=2m ./internal/observe ./cmd/fsn-observe > "$results/tests.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
[[ "$result" == 0 ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build -race -mod=readonly -o tmp/restart-observer-tickets/fsn-observe ./cmd/fsn-observe > "$results/build.txt" 2>&1
sha256sum tmp/restart-observer-tickets/fsn-observe > "$results/binary.sha256"
tail -n 6 "$results/tests.txt"
