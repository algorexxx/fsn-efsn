#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source="$workspace/tmp/recovery-signing-linux-v2-src"
cp "$workspace/ethdb/leveldb/readonly_test.go" "$source/ethdb/leveldb/readonly_test.go"
cd "$source"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -v ./ethdb/leveldb > "$workspace/docs/evidence/restart-signing-journal-2026-09-24/linux-readonly-manifest-race.txt" 2>&1
tail -n 5 "$workspace/docs/evidence/restart-signing-journal-2026-09-24/linux-readonly-manifest-race.txt"
