#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-discovery-2026-09-25"
cd "$workspace"
unshare --net -- bash -c 'set -e; ip link set lo up; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -timeout=3m ./p2p/discover ./p2p' bash "$workspace" > "$results/package-race.txt" 2>&1
cat "$results/package-race.txt"
