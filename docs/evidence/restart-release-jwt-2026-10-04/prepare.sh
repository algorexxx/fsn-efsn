#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-jwt-2026-10-04
work=/home/rehearsal/results/restart-release-jwt-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$work"
python3 - <<'PY'
import shutil
assert shutil.disk_usage('/home/rehearsal').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
mkdir -p "$work/download" "$work/bin" "$work/tmp"
cd "$work/download"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GO111MODULE=on GOFLAGS= GOMAXPROCS=2
export GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
date -u +%FT%TZ > "$evidence/download-started.txt"
timeout --signal=TERM --kill-after=10s 3m go mod download -json github.com/golang-jwt/jwt/v4@v4.5.2 > "$evidence/module-download.json" 2> "$evidence/module-download.stderr.txt"
go env GOPROXY GOSUMDB GOMOD GOWORK > "$evidence/download-environment.txt"
date -u +%FT%TZ > "$evidence/download-finished.txt"
