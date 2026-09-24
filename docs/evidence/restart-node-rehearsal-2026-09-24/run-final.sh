#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-node-rehearsal
results=/home/rehearsal/results/restart-node-rehearsal-2026-09-24/final
test -d "$source"
test ! -e "$results"
mkdir "$results"
cp "$workspace/core/restart_anchor.go" "$source/core/restart_anchor.go"
cp "$workspace/tests/restart/node_rehearsal_linux_test.go" "$source/tests/restart/node_rehearsal_linux_test.go"
chown -R rehearsal:rehearsal "$source" "$results"
cd "$source"
export PATH=/opt/fusion-toolchain/go/bin:$PATH
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly -c -o "$results/node-tests" ./tests/restart > "$results/build-tests.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go build -p=2 -mod=readonly -o "$results/efsn" ./cmd/efsn > "$results/build-node.txt" 2>&1
{
    date -u +%FT%TZ
    go version
    gcc --version | head -n 1
    sha256sum "$results/node-tests" "$results/efsn"
    sha256sum core/restart_anchor.go tests/restart/node_rehearsal_linux_test.go
} > "$results/identity.txt"
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 GOMAXPROCS=2 "$1" -test.v -test.timeout=10m' bash "$results/node-tests" > "$results/full-race.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/full-exit-code.txt"
if [ "$code" -eq 0 ]; then
    unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env FUSION_RESTART_NODE_REHEARSAL=1 GOMAXPROCS=2 "$1" -test.run=^TestRestartNodeRehearsal$ -test.v -test.count=2 -test.timeout=6m' bash "$results/node-tests" > "$results/node-race-2.txt" 2>&1
    code=$?
    printf '%s\n' "$code" > "$results/node-exit-code.txt"
fi
date -u +%FT%TZ > "$results/finished.txt"
tail -n 8 "$results/full-race.txt"
exit "$code"
