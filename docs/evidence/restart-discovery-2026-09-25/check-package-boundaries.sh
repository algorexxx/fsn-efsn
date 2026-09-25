#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-discovery-2026-09-25"
cd "$workspace"
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -overlay="$1/tmp/discovery-pre-p10-overlay/overlay.json" -count=1 -run="^(TestParseNode|TestForwardCompatibility|TestProtocolHandshake)$" -timeout=1m ./p2p/discover ./p2p' bash "$workspace" > "$results/package-baseline-failures.txt" 2>&1
status=$?
set -e
printf 'baseline failing-test command exit=%s\n' "$status"
if [ "$status" -ne 1 ]; then exit 2; fi
if [ "${1:-}" = failures-only ]; then exit 0; fi
unshare --net -- bash -c 'set -e; ip link set lo up; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -count=1 -run="^(TestTable_|TestBucket_|TestUDP_|TestDial|TestServer)" -timeout=3m ./p2p/discover ./p2p' bash "$workspace" > "$results/package-focused-race.txt" 2>&1
cat "$results/package-focused-race.txt"
