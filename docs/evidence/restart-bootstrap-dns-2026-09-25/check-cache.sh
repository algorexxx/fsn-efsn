#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-bootstrap-dns-2026-09-25"
label=${1:-current}
case "$label" in before|current) ;; *) exit 2;; esac
overlay=()
if [ "$label" = before ]; then
    overlay+=("-overlay=$workspace/tmp/bootstrap-cache-before/overlay.json")
fi
cd "$workspace"
unshare --net -- runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly "${overlay[@]}" -count=1 -run='^TestRestartBootstrapRefreshKeepsResolvedAddress$' -v -timeout=30s ./p2p/discover > "$results/cache-$label.txt" 2>&1
cat "$results/cache-$label.txt"
