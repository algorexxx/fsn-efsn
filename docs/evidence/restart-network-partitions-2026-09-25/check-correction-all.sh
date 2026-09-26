#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
results="$workspace/docs/evidence/restart-network-partitions-2026-09-25"
cd "$workspace"
date -u +%FT%TZ > "$results/correction-started.txt"
if bash "$results/check-correction.sh" live-before; then
  printf 'Unexpected baseline success\n'
  exit 1
fi
bash "$results/check-correction.sh" live-after
if bash "$results/check-correction.sh" broad; then
  printf 'Full affected suites passed\n'
fi
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 GOOS=windows GOARCH=amd64 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -p=2 -mod=readonly -c -o "$workspace/tmp/network-self-windows-tests.exe" ./p2p/discover > "$results/windows-build.txt" 2>&1
bash "$results/check-correction.sh" partitions
