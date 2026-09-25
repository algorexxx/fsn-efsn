#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-peer-addresses-2026-09-25"
cd "$workspace"
for mode in after regressions live-after; do
  bash "$results/check.sh" "$mode"
done
if bash "$results/check.sh" broad; then
  printf 'Full affected suites passed\n'
fi
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 GOOS=windows GOARCH=amd64 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -p=2 -mod=readonly -c -o "$workspace/tmp/peer-addresses-windows-tests.exe" ./p2p/discover > "$results/windows-build.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go build -race -p=2 -mod=readonly -o "$workspace/tmp/peer-addresses-efsn" ./cmd/efsn > "$results/efsn-build.txt" 2>&1
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -race -p=2 -mod=readonly -c -o "$workspace/tmp/peer-addresses-dns-tests" ./tests/restart > "$results/dns-build.txt" 2>&1
cd tests/restart
unshare --net -- bash -c 'set -e; ip link set lo up; ip -brief link; exec runuser -u rehearsal -- env GOMAXPROCS=2 TMPDIR=/tmp FUSION_RESTART_CHAINDATA= FUSION_RESTART_DISCOVERY_REHEARSAL=1 FUSION_RESTART_DNS_BINARY="$1/tmp/peer-addresses-efsn" "$1/tmp/peer-addresses-dns-tests" "-test.run=^TestRestartBootstrapDNSRehearsal$" -test.v -test.timeout=3m' bash "$workspace" > "$results/dns-race.txt" 2>&1
tail -n 18 "$results/dns-race.txt"
