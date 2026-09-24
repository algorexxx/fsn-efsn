#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-offline-signing-2026-09-24"
binary="$workspace/tmp/recovery-offline-linux-tests"
temporary="$workspace/tmp/recovery-guard-linux-gotmp"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" TMPDIR="$temporary" go test -race -p=2 -mod=readonly -count=1 -v ./internal/recovery ./cmd/fsn-recovery > "$results/linux-unit-final-race.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$temporary" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR="$temporary" "$binary" '-test.run=^Test(OfflineRecovery(ProcessCuts|UncertainCuts|Refusals)|Recovery(Guard|GuardRejects|GuardInsufficientReplacement|JournalHandover))$' -test.v -test.timeout=3m > "$results/linux-integration-race.txt" 2>&1
tail -n 8 "$results/linux-integration-race.txt"
