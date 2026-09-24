#!/bin/bash
set -euo pipefail
results=/home/rehearsal/results/restart-rewind-rehearsal-2026-09-24
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-rewind-rehearsal-2026-09-24
test -f "$results/finished.txt"
read -r full_code < "$results/full-exit-code.txt"
read -r rewind_code < "$results/rewind-exit-code.txt"
test "$full_code" = 0
test "$rewind_code" = 0
for name in build-tests.txt build-node.txt identity.txt full-race.txt full-exit-code.txt rewind-race-2.txt rewind-exit-code.txt finished.txt; do
    cp "$results/$name" "$evidence/linux-$name"
done
{
    date -u +%FT%TZ
    tail -n 4 /home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24/replay.txt
    df -B1 /home/rehearsal
    sha256sum /home/rehearsal/replay-resume-tests
} > "$evidence/replay-progress.txt"
cat "$evidence/replay-progress.txt"
