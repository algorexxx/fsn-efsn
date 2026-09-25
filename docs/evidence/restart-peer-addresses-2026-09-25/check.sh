#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-peer-addresses-2026-09-25"
cd "$workspace"
mode=${1:?before, after, regressions, broad, live-before, or live-after}
overlay=
if [[ "$mode" == *before ]]; then
  overlay="-overlay=$workspace/tmp/peer-addresses-before/overlay.json"
fi
case "$mode" in
  before|after) pattern='^TestRestartPeer(Address|Replacement|Stale|Repeated)' ;;
  regressions) pattern='^(TestRestartBootstrap|TestExplicitEmptyBootstrapNodes|TestRestartPeer|TestRestartSparse|TestTable_|TestBucket_|TestUDP_|TestNodeDB|TestDial|TestServer)' ;;
  broad) pattern='.' ;;
  live-before|live-after) pattern='^TestRestartPeerAddressLive$' ;;
  *) exit 2 ;;
esac
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; if [[ "$4" == live-* ]]; then ip address add 172.0.1.1/16 dev lo; ip address add 172.0.2.1/16 dev lo; ip address add 172.0.3.1/16 dev lo; ip -brief address; export FUSION_RESTART_ADDRESS_REHEARSAL=1; fi; exec runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$1/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly ${3:+"$3"} -count=1 -v -run="$2" -timeout=4m ./p2p/discover ./p2p ./cmd/utils' bash "$workspace" "$pattern" "$overlay" "$mode" > "$results/$mode-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/$mode-exit.txt"
tail -n 45 "$results/$mode-race.txt"
exit "$status"
