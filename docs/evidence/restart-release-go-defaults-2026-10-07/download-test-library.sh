#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-go-defaults-2026-10-07
work=/home/rehearsal/results/restart-release-go-defaults-2026-10-07
export PATH=/home/rehearsal/results/restart-release-selection-2026-10-04/toolchain/go/bin:/usr/bin:/bin
export GOTOOLCHAIN=local GOWORK=off GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
unset GOFLAGS GODEBUG GOEXPERIMENT
phase=${1:-initial}
test "$phase" = initial || test "$phase" = transitive || test "$phase" = corrected
if [ "$phase" = initial ]; then mkdir "$work/download"; fi
label=test-library-download
modules=gopkg.in/check.v1@v1.0.0-20201130134442-10cb98267c6c
if [ "$phase" = transitive ]; then
    label=test-library-transitive-download
    modules="github.com/kr/pretty@v0.3.0 github.com/kr/text@v0.2.0 github.com/rogpeppe/go-internal@v1.9.0"
fi
if [ "$phase" = corrected ]; then
    label=test-library-corrected-download
    modules=github.com/rogpeppe/go-internal@v1.6.1
fi
test ! -e "$evidence/$label-started.txt"
cd "$work/download"
date -u +%FT%TZ > "$evidence/$label-started.txt"
go env GOMOD GOWORK GOPROXY GOSUMDB GOMODCACHE > "$evidence/$label-environment.txt"
set +e
timeout --signal=TERM --kill-after=10s 90s go mod download -json $modules > "$evidence/$label.json" 2> "$evidence/$label.stderr.txt"
code=$?
set -e
printf '%s\n' "$code" > "$evidence/$label-exit.txt"
test "$code" = 0
date -u +%FT%TZ > "$evidence/$label-finished.txt"
