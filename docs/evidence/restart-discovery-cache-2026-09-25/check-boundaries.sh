#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-discovery-cache-2026-09-25"
label=${1:-current}
case "$label" in baseline|current) ;; *) exit 2 ;; esac
build_options=()
if [ "$label" = baseline ]; then
    build_options+=("-overlay=$workspace/tmp/discovery-cache-baseline-overlay/overlay.json")
fi
cd "$workspace"
unshare --net -- runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly "${build_options[@]}" -count=1 -run='^TestRestartPeer' -v -timeout=1m ./p2p/discover > "$results/boundaries-$label.txt" 2>&1
tail -n 12 "$results/boundaries-$label.txt"
