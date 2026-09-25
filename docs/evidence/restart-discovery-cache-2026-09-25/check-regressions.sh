#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-discovery-cache-2026-09-25"
cd "$workspace"
unshare --net -- runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -run='^(TestRestartPeer|TestRestartSparse|TestTable_|TestBucket_|TestUDP_|TestNodeDB)' -timeout=3m ./p2p/discover > "$results/regressions-race.txt" 2>&1
cat "$results/regressions-race.txt"
