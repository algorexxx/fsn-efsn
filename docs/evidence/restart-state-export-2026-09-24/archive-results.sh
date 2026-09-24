#!/bin/bash
set -euo pipefail
base=/home/rehearsal/results/restart-state-export-2026-09-24
replay=/home/rehearsal/results/restart-replay-checkpoint-boundary-2026-09-24
replay_c=/home/rehearsal/results/restart-replay-c-storage-2026-09-24
evidence=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-export-2026-09-24
target=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/preserved-head-state
test "$(cat "$base/c-storage/export-exit-code.txt")" = 0
test "$(cat "$evidence/windows-verify-exit-code.txt")" = 0
test -f "$base/c-storage/finished.txt"
test -f "$target/verified.json"
python3 "$evidence/verify-identities.py"
for path in "$base"/*.txt; do
    cp "$path" "$evidence/linux-$(basename "$path")"
done
for path in "$base/c-storage"/*.txt; do
    cp "$path" "$evidence/c-$(basename "$path")"
done
for name in replay.txt exit-code.txt finished.txt size.txt capacity-after.txt; do
    cp "$replay/$name" "$evidence/replay-$name"
done
for name in copy-manifest.json copy-verified.txt started.txt isolation.txt capacity-before.txt; do
    cp "$replay_c/$name" "$evidence/replay-c-$name"
done
if [ -f "$replay_c/finished.txt" ]; then
    for name in replay.txt exit-code.txt finished.txt size.txt capacity-after.txt cold-head-check.txt; do
        cp "$replay_c/$name" "$evidence/replay-c-$name"
    done
else
    {
        date -u +%FT%TZ
        tail -n 8 "$replay_c/replay.txt"
    } > "$evidence/replay-c-progress.txt"
fi
cp "$target/identity.json" "$evidence/artifact-identity.json"
cp "$target/verified.json" "$evidence/artifact-verified.json"
cp /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-mainnet-c/replay-identity.json "$evidence/replay-identity.json"
cd "$target"
find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$evidence/artifact-SHA256SUMS"
sha256sum --check "$evidence/artifact-SHA256SUMS" > "$evidence/artifact-checksums-verified.txt"
du -sb "$target" > "$evidence/artifact-total-size.txt"
du -sb "$target/chaindata" > "$evidence/artifact-database-size.txt"
date -u +%FT%TZ > "$evidence/archived.txt"
