#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-snapshot-framing-2026-09-27/after-linux"
[[ ! -e "$results" ]]
mkdir "$results"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
cd "$workspace"
ip link set lo up
ip -brief link > "$results/network.txt"
go version > "$results/toolchain.txt"
sha256sum consensus/datong/snapshot{,_test}.go tests/restart/*_test.go go.mod go.sum docs/evidence/restart-2026-09-23/responses.json > "$results/sources.sha256"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -count=1 -p=2 -mod=readonly -v -timeout=1m ./consensus/datong > "$results/parser-race.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -count=1 -p=2 -mod=readonly -v -timeout=3m -run '^(TestHeaderBatchUsesUnstoredParents|TestFinalizeParentIsolatedFromConcurrentImport|TestColdHeaderValidationBoundaries)$' ./tests/restart > "$results/compatibility-race.txt" 2>&1
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test -race -mod=readonly -run '^$' -fuzz '^FuzzSnapshotFraming$' -fuzztime=10s -parallel=2 -timeout=1m ./consensus/datong > "$results/fuzz-race.txt" 2>&1
printf '0\n' > "$results/exit.txt"
tail -n 6 "$results/fuzz-race.txt"
