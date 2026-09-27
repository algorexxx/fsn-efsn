#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-services-2026-09-27"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
results="$evidence/$attempt"
[[ ! -e "$results" ]]
mkdir "$results"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
df -B1 /tmp /mnt/d > "$results/capacity-before.txt"
go version > "$results/toolchain.txt"
git -c safe.directory="$workspace" rev-parse HEAD > "$results/baseline.txt"
sha256sum cmd/fsn-observe/*.go internal/observe/*.go tests/restart/*_test.go > "$results/sources.sha256"
mkdir -p tmp/restart-observer-services
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -p=2 -mod=readonly -c -o tmp/restart-observer-services/services-tests ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build -race -mod=readonly -o tmp/restart-observer-services/fsn-observe ./cmd/fsn-observe > "$results/build-observer.txt" 2>&1
sha256sum tmp/restart-observer-services/{services-tests,fsn-observe} > "$results/binaries.sha256"
set +e
cd tests/restart
env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NODE_REHEARSAL=1 FUSION_RESTART_NETWORK_PARTITION=1 FUSION_RESTART_OBSERVER_BIN="$workspace/tmp/restart-observer-services/fsn-observe" FUSION_RESTART_OBSERVER_RESULTS="$results/services" "$workspace/tmp/restart-observer-services/services-tests" -test.run='^TestObserverNodeServices$' -test.v -test.timeout=4m > "$results/services-race.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/exit.txt"
df -B1 /tmp /mnt/d > "$results/capacity-after.txt"
tail -n 12 "$results/services-race.txt"
exit "$result"
