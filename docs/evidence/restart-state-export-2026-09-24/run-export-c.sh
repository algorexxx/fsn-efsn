#!/bin/bash
set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-state-export
base=/home/rehearsal/results/restart-state-export-2026-09-24
results="$base/c-storage"
target=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/preserved-head-state
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test -f "$base/export-tests"
test ! -e "$target"
test ! -e "$results"
mkdir "$results"
mkdir -p "$mountpoint"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
findmnt -no TARGET,FSTYPE,OPTIONS -T "$(dirname "$target")" >> "$results/isolation.txt"
ip -brief link >> "$results/isolation.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-before.txt"
date -u +%FT%TZ > "$results/started.txt"
cd /home/rehearsal/fsn-efsn-state-export/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_STATE_EXPORT_DIR="$target" FUSION_RESTART_STATE_EXPORT_STOP_FILE=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/STOP-state-export FUSION_RESTART_HOST_STORAGE=/mnt/c GOMAXPROCS=2 "$base/export-tests" '-test.run=^TestPreservedStateExport$' -test.v -test.timeout=2h > "$results/export.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/export-exit-code.txt"
umount "$mountpoint"
if [ "$code" -eq 0 ]; then
    runuser -u rehearsal -- env -u FUSION_RESTART_CHAINDATA FUSION_RESTART_VERIFY_EXPORT_DIR="$target" GOMAXPROCS=2 "$base/export-tests" '-test.run=^TestVerifyStateExport$' -test.v -test.timeout=1h > "$results/verify.txt" 2>&1
    code=$?
    printf '%s\n' "$code" > "$results/verify-exit-code.txt"
fi
date -u +%FT%TZ > "$results/finished.txt"
du -sb "$target" "$target/chaindata" > "$results/size.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 8 "$results/export.txt"
if [ -f "$results/verify.txt" ]; then tail -n 8 "$results/verify.txt"; fi
exit "$code"
