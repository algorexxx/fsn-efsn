#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-followup-2026-10-04"
work=/home/rehearsal/results/restart-release-followup-2026-10-04
compiler=/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go
test ! -e "$work"
python3 - <<'PY'
import shutil
assert shutil.disk_usage('/home/rehearsal').free > 30 * 1024**3
assert shutil.disk_usage('/mnt/d').free > 60 * 1024**3
PY
mkdir -p "$work/bin" "$work/gopath" "$work/cache" "$work/tmp"
export PATH="$compiler/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOMAXPROCS=2 CGO_ENABLED=1
export GOPATH="$work/gopath" GOBIN="$work/bin" GOCACHE="$work/cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
export GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
date -u +%FT%TZ > "$evidence/scanner-prepare-started.txt"
set +e
timeout --signal=TERM --kill-after=20s 8m go install -p=2 golang.org/x/vuln/cmd/govulncheck@v1.8.0 > "$evidence/scanner-install.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/scanner-install-exit.txt"
test "$code" = 0
go version -m "$work/bin/govulncheck" > "$evidence/scanner-build-info.txt"
sha256sum "$work/bin/govulncheck" > "$evidence/scanner-binary.sha256"
"$work/bin/govulncheck" -version > "$evidence/scanner-version.txt" 2>&1
date -u +%FT%TZ > "$evidence/scanner-prepared.txt"
