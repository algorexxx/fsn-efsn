#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-observer-history-2026-09-27"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
[[ ! -e "$results/linux-race.txt" ]]
mkdir "$results/linux-history"
mkdir -p tmp/restart-observer-history
ip link set lo up
ip -brief link > "$results/linux-network.txt"
go version > "$results/linux-toolchain.txt"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp FUSION_OBSERVE_EVIDENCE= FUSION_HISTORY_EVIDENCE="$results/linux-history" go test -count=1 -race -p=2 -mod=readonly -v -timeout=2m ./internal/observe ./cmd/fsn-observe > "$results/linux-race.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go build -mod=readonly -o tmp/restart-observer-history/fsn-observe-linux ./cmd/fsn-observe > "$results/linux-build.txt" 2>&1
sha256sum tmp/restart-observer-history/fsn-observe-linux > "$results/linux-binary.sha256"
