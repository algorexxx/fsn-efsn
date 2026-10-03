#!/bin/bash
set -euo pipefail
workspace=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn
evidence="$workspace/docs/evidence/restart-observer-open-replay-2026-10-03"
attempt="${1:?explicit attempt name required}"
[[ "$attempt" =~ ^attempt-[1-9][0-9]*$ ]]
export PATH=/opt/fusion-toolchain/go/bin:/usr/sbin:/usr/bin:/bin
ip link set lo up
for variant in baseline candidate; do
    results="$evidence/$attempt/comparison/$variant"
    [[ ! -e "$results" ]]
    mkdir -p "$results"
    cp "$evidence/compare-linux.sh" "$results/compare-linux.sh"
    cp "$evidence/$variant/sources.sha256" "$results/effective-sources.sha256"
    flags=()
    if [[ "$variant" == baseline ]]; then
        printf '{"Replace":{"%s/internal/observe/history.go":"%s/baseline/history.go.txt","%s/internal/observe/history_open_test.go":""}}\n' "$workspace" "$evidence" "$workspace" > "$results/overlay.json"
        flags=(-overlay "$results/overlay.json")
    fi
    build="/tmp/fusion-observer-compare-$attempt-$variant"
    mkdir "$build"
    chown rehearsal "$build"
    cd "$workspace"
    runuser -u rehearsal -- env PATH="$PATH" GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2 GOTMPDIR=/tmp go test "${flags[@]}" -mod=readonly -c -o "$build/observe-tests" ./internal/observe > "$results/build.txt" 2>&1
    sha256sum "$build/observe-tests" > "$results/binary.sha256"
    cd internal/observe
    set +e
    env GOMAXPROCS=2 TMPDIR=/tmp FUSION_HISTORY_EVIDENCE="$results" FUSION_BACKFILL_EVIDENCE="$results" FUSION_TICKET_EVIDENCE="$results" "$build/observe-tests" -test.run='^(TestHistoryRetainedServiceTransitions|TestBackfillRetainedForkAndResume|TestTicketTimelineRetainedMiningAndColdRead)$' -test.v -test.timeout=2m > "$results/tests.txt" 2>&1
    result=$?
    set -e
    printf '%s\n' "$result" > "$results/test-exit.txt"
    [[ "$result" == 0 ]]
done
