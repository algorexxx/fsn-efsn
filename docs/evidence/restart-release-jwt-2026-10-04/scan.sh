#!/bin/bash
set -euo pipefail
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-jwt-2026-10-04
work=/home/rehearsal/results/restart-release-jwt-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
scanner=/home/rehearsal/results/restart-release-followup-2026-10-04
test -s "$evidence/qualification-finished.txt"
test ! -e "$evidence/scans-started.txt"
test "$(sha256sum "$scanner/bin/govulncheck" | cut -d ' ' -f 1)" = 305a4977e2a2615e3f30e5ecad5651e714daf5339ac95c2712895e4f974da54f
test "$(sha256sum "$scanner/vulndb.zip" | cut -d ' ' -f 1)" = a601a35d09bb8daee2acea8c7944b1964df1d87f4f3611efd2ee754b5e470f39
export PATH="$selected/toolchain/go/bin:/usr/bin:/bin"
export GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
export CGO_ENABLED=1 GOAMD64=v1 GOMAXPROCS=2 GOMEMLIMIT=2GiB
export GOCACHE="$selected/repeat-cache" GOTMPDIR="$work/tmp" TMPDIR="$work/tmp"
date -u +%FT%TZ > "$evidence/scans-started.txt"
ip -brief link > "$evidence/scan-network.txt"
for name in efsn fsn-recovery; do
    if [ "$name" = efsn ]; then folder=node; else folder=recovery; fi
    cd "$work/$folder"
    sha256sum -c "$evidence/binary-$name.sha256"
    for mode in binary source; do
        if [ "$mode" = binary ]; then target="$work/bin/$name"; else target="./cmd/$name"; fi
        set +e
        timeout --signal=TERM --kill-after=20s 10m "$scanner/bin/govulncheck" -db="file://$scanner/vulndb" -mode="$mode" -format=json "$target" > "$evidence/$mode-$name.json" 2> "$evidence/$mode-$name.stderr.txt"
        code=$?
        set -e
        printf '%s\n' "$code" > "$evidence/$mode-$name-exit.txt"
        test "$code" = 0
    done
done
date -u +%FT%TZ > "$evidence/scans-finished.txt"
