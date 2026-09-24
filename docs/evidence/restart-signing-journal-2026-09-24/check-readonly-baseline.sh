#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/recovery-signing-linux-v2-src"
baseline="$source/tmp/readonly-manifest-baseline"
test ! -e "$baseline"
mkdir -p "$baseline"
tar -xOf "$workspace/tmp/recovery-signing-base.tar" ethdb/leveldb/leveldb.go > "$baseline/leveldb.go"
cp "$workspace/ethdb/leveldb/readonly_test.go" "$baseline/readonly_test.go"
cd "$source"
set +e
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -p=2 -mod=readonly -count=1 -v ./tmp/readonly-manifest-baseline > "$workspace/docs/evidence/restart-signing-journal-2026-09-24/readonly-manifest-baseline-counterexample.txt" 2>&1
result=$?
set -e
cat "$workspace/docs/evidence/restart-signing-journal-2026-09-24/readonly-manifest-baseline-counterexample.txt"
test "$result" -eq 1
