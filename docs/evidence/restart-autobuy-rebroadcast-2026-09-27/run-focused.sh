#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-autobuy-rebroadcast-2026-09-27"
binary="$workspace/tmp/autobuy-rebroadcast-2026-09-27"
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
mkdir -p "$binary"
cd "$workspace"
[[ ! -e "$results/focused.txt" ]]
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -v ./internal/ethapi > "$results/focused.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/focused-exit.txt"
tail -n 18 "$results/focused.txt"
[[ "$status" == 0 ]]
cd "$workspace/eth"
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off go list -f '{{join .GoFiles " "}}' . > "$results/production-files.txt"
read -r -a sources < "$results/production-files.txt"
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -v "${sources[@]}" autobuy_retry_test.go > "$results/peer-focused.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/peer-focused-exit.txt"
tail -n 18 "$results/peer-focused.txt"
exit "$status"
