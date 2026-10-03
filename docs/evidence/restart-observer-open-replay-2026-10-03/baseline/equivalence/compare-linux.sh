#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-open-replay-2026-10-03"
ip link set lo up
cd "$workspace/internal/observe"
for variant in baseline candidate; do
    results="$evidence/$variant/equivalence"
    [[ ! -e "$results" ]]
    mkdir "$results"
    cp "$evidence/compare-linux.sh" "$results/compare-linux.sh"
    set +e
    env GOMAXPROCS=2 TMPDIR=/tmp FUSION_HISTORY_EVIDENCE="$results" FUSION_BACKFILL_EVIDENCE="$results" FUSION_TICKET_EVIDENCE="$results" "/tmp/fusion-observer-open-replay-$variant/observe-tests" -test.run='^(TestHistoryRetainedServiceTransitions|TestBackfillRetainedForkAndResume|TestTicketTimelineRetainedMiningAndColdRead)$' -test.v -test.timeout=2m > "$results/tests.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/test-exit.txt"
    [[ "$result" == 0 ]]
done
