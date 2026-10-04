#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-selection-2026-10-04"
work=/home/rehearsal/results/restart-release-selection-2026-10-04
test ! -e "$evidence/handshake-loopback-before.txt"
ip -brief link > "$evidence/handshake-network.txt"
export PATH="$work/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2
export GOCACHE="$work/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
cd "$work/repeat"
set +e
timeout --signal=TERM --kill-after=20s 5m go test -p=2 -count=1 -run '^TestProtocolHandshake$' -timeout=90s -v ./p2p > "$evidence/handshake-loopback-before.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/handshake-loopback-before-exit.txt"
test "$code" = 1
grep -q 'message size mismatch: got 2, want 1' "$evidence/handshake-loopback-before.txt"
git apply --check "$evidence/06-handshake-fixture.patch"
git apply "$evidence/06-handshake-fixture.patch"
set +e
timeout --signal=TERM --kill-after=20s 5m go test -race -p=2 -count=1 -run '^TestProtocolHandshake$' -timeout=90s -v ./p2p > "$evidence/handshake-loopback-after.txt" 2>&1
code=$?
set -e
printf '%s\n' "$code" > "$evidence/handshake-loopback-after-exit.txt"
test "$code" = 0
tail -n 5 "$evidence/handshake-loopback-after.txt"
