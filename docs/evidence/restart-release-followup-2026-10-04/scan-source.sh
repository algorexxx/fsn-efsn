#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-followup-2026-10-04"
previous="$workspace/docs/evidence/restart-release-selection-2026-10-04"
work=/home/rehearsal/results/restart-release-followup-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test -s "$evidence/binary-scan-finished.txt"
test ! -e "$evidence/source-scan-started.txt"
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly CGO_ENABLED=1 GOMAXPROCS=2 GOMEMLIMIT=2GiB
export GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
date -u +%FT%TZ > "$evidence/source-scan-started.txt"
ip -brief link > "$evidence/source-scan-network.txt"
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=source; else folder=repeat; fi
    cd "$selected/$folder"
    sha256sum go.mod go.sum > "$evidence/source-$name-modules-before.sha256"
    set +e
    timeout --signal=TERM --kill-after=20s 10m "$work/bin/govulncheck" -db="file://$work/vulndb" -format=json "./cmd/$name" > "$evidence/source-$name.json" 2> "$evidence/source-$name.stderr.txt"
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/source-$name-exit.txt"
    sha256sum go.mod go.sum > "$evidence/source-$name-modules-after.sha256"
    cmp "$evidence/source-$name-modules-before.sha256" "$evidence/source-$name-modules-after.sha256"
done
date -u +%FT%TZ > "$evidence/source-scan-finished.txt"
