#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-release-followup-2026-10-04"
work=/home/rehearsal/results/restart-release-followup-2026-10-04
selected=/home/rehearsal/results/restart-release-selection-2026-10-04
test -s "$evidence/scanner-prepared.txt"
test -s "$evidence/database-snapshot.json"
test ! -e "$evidence/binary-scan-started.txt"
export GOMAXPROCS=2 GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off
test "$(sha256sum "$selected/bin/efsn" | cut -d ' ' -f 1)" = ab9c8ff071568bc21466e030a7ae3895a3c7a085559df28389248bec24c0632d
test "$(sha256sum "$selected/bin/fsn-recovery" | cut -d ' ' -f 1)" = 655c0882b68e7cb5b97caf168c1b7a9bac8af3cb03802a0559a28b384dd88407
date -u +%FT%TZ > "$evidence/binary-scan-started.txt"
ip -brief link > "$evidence/scan-network.txt"
for name in efsn fsn-recovery; do
    set +e
    timeout --signal=TERM --kill-after=20s 10m "$work/bin/govulncheck" -db="file://$work/vulndb" -mode=binary -format=json "$selected/bin/$name" > "$evidence/binary-$name.json" 2> "$evidence/binary-$name.stderr.txt"
    code=$?
    set -e
    printf '%s\n' "$code" > "$evidence/binary-$name-exit.txt"
    test "$code" = 0
done
date -u +%FT%TZ > "$evidence/binary-scan-finished.txt"
