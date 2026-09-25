#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-bootstrap-dns-2026-09-25"
mode=${1:-dns}
case "$mode" in dns) filter='^TestRestartBootstrapDNSRehearsal$';; full) filter='^TestRestart(BootstrapDNSRehearsal|DiscoveryRehearsal)$';; *) exit 2;; esac
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go build -race -p=2 -mod=readonly -o "$workspace/tmp/bootstrap-dns-efsn" ./cmd/efsn > "$results/$mode-build.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$workspace/tmp/bootstrap-dns-tests" ./tests/restart >> "$results/$mode-build.txt" 2>&1
cd tests/restart
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_DISCOVERY_REHEARSAL=1 FUSION_RESTART_DNS_CACHE=1 FUSION_RESTART_DNS_BINARY="$1/tmp/bootstrap-dns-efsn" "$1/tmp/bootstrap-dns-tests" "-test.run=$2" -test.v -test.timeout=13m' bash "$workspace" "$filter" > "$results/$mode-race.txt" 2>&1
tail -n 22 "$results/$mode-race.txt"
