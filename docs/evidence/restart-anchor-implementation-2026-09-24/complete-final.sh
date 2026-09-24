#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
source=/home/rehearsal/fsn-efsn-anchor-implementation
results=/home/rehearsal/results/restart-anchor-implementation-2026-09-24/final
test -x "$results/anchor-tests"
test -x "$results/efsn"
test ! -e "$results/anchor-race-3.txt"
export PATH=/opt/fusion-toolchain/go/bin:$PATH
cd /home/rehearsal/fsn-efsn-anchor
set +e
runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 go test -race -p=2 -mod=readonly ./core/rawdb -run '^$' > "$results/rawdb-baseline-build.txt" 2>&1
printf '%s\n' "$?" > "$results/rawdb-baseline-exit-code.txt"
set -e
cd "$source"
{
    date -u +%FT%TZ
    go version
    gcc --version | head -n 1
    sha256sum "$results/anchor-tests" "$results/efsn"
    while IFS= read -r path; do sha256sum "$path"; done < <(tr -d '\r' < "$workspace/docs/evidence/restart-anchor-implementation-2026-09-24/source-files.txt")
} > "$results/identity.txt"
cd tests/restart
set +e
unshare --net -- runuser -u rehearsal -- "$results/anchor-tests" '-test.run=^TestRestart(Anchor|Rollback)' -test.v -test.count=3 -test.timeout=8m > "$results/anchor-race-3.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/exit-code.txt"
date -u +%FT%TZ > "$results/finished.txt"
tail -n 8 "$results/anchor-race-3.txt"
exit "$code"
