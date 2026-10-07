#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-go-defaults-2026-10-07"
candidate=/home/rehearsal/results/restart-release-text-2026-10-04
baseline=/home/rehearsal/results/restart-release-jwt-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
phase=${1:-initial}
test "$phase" = initial || test "$phase" = cached || test "$phase" = complete || test "$phase" = corrected
runlabel=tests
networklabel=test-network
if [ "$phase" != initial ]; then runlabel="tests-$phase"; networklabel="test-$phase-network"; fi
test ! -e "$evidence/$runlabel-started.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOCACHE="$selected/repeat-cache"
export GOTMPDIR="$candidate/tmp" TMPDIR="$candidate/tmp"
unset GODEBUG GOEXPERIMENT
date -u +%FT%TZ > "$evidence/$runlabel-started.txt"
ip -brief link > "$evidence/$networklabel.txt"
for stage in baseline candidate; do
    if [ "$stage" = baseline ]; then cd "$baseline/node"; else cd "$candidate/node"; fi
    packages="common rlp core/types core/state"
    if [ "$phase" != initial ]; then packages="common core/state"; fi
    for package in $packages; do
        label="${stage}-${package//\//-}"
        if [ "$phase" != initial ]; then label="$label-$phase"; fi
        set +e
        timeout --signal=TERM --kill-after=20s 7m go test -race -p=2 -count=1 -timeout=5m -v "./$package" > "$evidence/$label.txt" 2>&1
        code=$?
        set -e
        printf '%s\n' "$code" > "$evidence/$label-exit.txt"
        printf '%s exit=%s\n' "$label" "$code"
    done
done
date -u +%FT%TZ > "$evidence/$runlabel-finished.txt"
