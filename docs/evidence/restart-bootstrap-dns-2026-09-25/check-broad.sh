#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-bootstrap-dns-2026-09-25"
cd "$workspace"
set +e
unshare --net -- bash -c 'ip link set lo up; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -timeout=4m ./p2p/discover ./p2p ./cmd/utils' bash "$workspace" > "$results/broad-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/broad-exit.txt"
tail -n 20 "$results/broad-race.txt"
exit "$status"
