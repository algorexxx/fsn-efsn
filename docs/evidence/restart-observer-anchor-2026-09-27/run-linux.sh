#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-anchor-2026-09-27"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt/linux"
[[ ! -e "$results" ]]
mkdir -p "$results"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
df -B1 /tmp /mnt/d > "$results/capacity-before.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go > "$results/sources.sha256"
sha256sum tests/restart/*_test.go > "$results/test-sources.sha256"
mkdir -p tmp/restart-observer-anchor
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE= FUSION_BACKFILL_EVIDENCE= FUSION_TICKET_EVIDENCE= FUSION_ANCHOR_EVIDENCE="$results" go test -count=1 -race -p=2 -mod=readonly -v -timeout=2m ./internal/observe ./cmd/fsn-observe > "$results/tests.txt" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$results/test-exit.txt"
[[ "$result" == 0 ]]
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o tmp/restart-observer-anchor/services-tests ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build -race -mod=readonly -o tmp/restart-observer-anchor/fsn-observe ./cmd/fsn-observe > "$results/build.txt" 2>&1
sha256sum tmp/restart-observer-anchor/{services-tests,fsn-observe} > "$results/binaries.sha256"
set +e
cd tests/restart
env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_OBSERVER_BACKFILL=1 FUSION_RESTART_OBSERVER_ANCHOR=1 FUSION_RESTART_OBSERVER_BIN="$workspace/tmp/restart-observer-anchor/fsn-observe" FUSION_RESTART_OBSERVER_RESULTS="$results/services" "$workspace/tmp/restart-observer-anchor/services-tests" -test.run='^TestObserverNodeServices$' -test.v -test.timeout=4m > "$results/services-race.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/service-exit.txt"
df -B1 /tmp /mnt/d > "$results/capacity-after.txt"
tail -n 12 "$results/services-race.txt"
exit "$result"
