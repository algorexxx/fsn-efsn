#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/recovery-signing-linux-src"
results="$workspace/docs/evidence/restart-signing-journal-2026-09-24"
binary="$workspace/tmp/recovery-signing-linux-tests"
test ! -e "$source"
test ! -e "$binary"
mkdir "$source"
tar -xf "$workspace/tmp/recovery-signing-base.tar" -C "$source"
for file in internal/recovery/signing.go internal/recovery/signing_test.go consensus/datong/consensus.go ethdb/leveldb/leveldb.go ethdb/leveldb/readonly_test.go tests/restart/recovery_signing_test.go tests/restart/purchase_inventory_test.go; do
    cp "$workspace/$file" "$source/$file"
done
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -v ./internal/recovery ./ethdb/leveldb ./cmd/fsn-recovery > "$results/linux-unit-race.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$binary" ./tests/restart > "$results/linux-build.txt" 2>&1
cd tests/restart
unshare --net -- runuser -u rehearsal -- env GOMAXPROCS=2 "$binary" '-test.run=^TestRecovery(Guard|GuardRejects|GuardInsufficientReplacement|JournalHandover)$' -test.v -test.timeout=2m > "$results/linux-handover-race.txt" 2>&1
tail -n 8 "$results/linux-handover-race.txt"
