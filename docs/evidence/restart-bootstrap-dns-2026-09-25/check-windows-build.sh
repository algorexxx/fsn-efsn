#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
cd "$workspace"
runuser -u rehearsal -- env PATH=/opt/fusion-toolchain/go/bin:/usr/bin:/bin GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 GOOS=windows GOARCH=amd64 GOMAXPROCS=2 GOTMPDIR="$workspace/tmp/recovery-guard-linux-gotmp" go test -p=2 -mod=readonly -c -o "$workspace/tmp/bootstrap-dns-windows-tests.exe" ./p2p/discover > "$workspace/docs/evidence/restart-bootstrap-dns-2026-09-25/windows-build.txt" 2>&1
