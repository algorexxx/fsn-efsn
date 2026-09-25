#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-profile-2026-09-25"
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$workspace/tmp/network-profile-final-tests" ./tests/restart > "$results/final-build.txt" 2>&1
cd tests/restart
set +e
unshare --net -- bash -c 'set -e; ip link set lo up; ip address add 172.0.1.1/16 dev lo; ip -brief address; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_NETWORK_PROFILE=1 FUSION_RESTART_DISCOVERY_REHEARSAL=1 FUSION_RESTART_DNS_BINARY="$1/tmp/peer-addresses-efsn" "$1/tmp/network-profile-final-tests" "-test.run=^TestRestart(NetworkProfileRehearsal|NetworkConfigInputs|BootstrapDNSRehearsal)$" -test.v -test.timeout=3m' bash "$workspace" > "$results/final-live-race.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$results/final-live-exit.txt"
tail -n 30 "$results/final-live-race.txt"
exit "$status"
