#!/bin/bash
set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-replay-c-source
results=/home/rehearsal/results/restart-replay-c-storage-2026-09-24
target=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-mainnet-c
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test -f "$results/copy-verified.txt"
test ! -e "$results/started.txt"
test ! -e /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/STOP-replay-mainnet-c
test "$(sha256sum /home/rehearsal/replay-resume-tests | cut -d ' ' -f 1)" = 004d4eeb16fc27e68564ff34d18b5bb1c48829cb692b98770fe7c52543d26c1e
if pgrep -f '^/home/rehearsal/replay-resume-tests' >/dev/null; then exit 1; fi
exec 9>"$target.run.lock"
flock -n 9
mkdir -p "$mountpoint"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
findmnt -no TARGET,FSTYPE,OPTIONS -T "$target" >> "$results/isolation.txt"
ip -brief link >> "$results/isolation.txt"
sha256sum /home/rehearsal/replay-resume-tests "$target/replay-identity.json" "$results/copy-manifest.json" >> "$results/isolation.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-before.txt"
date -u +%FT%TZ > "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_RESUME=1 FUSION_RESTART_REPLAY_END=2700000 FUSION_RESTART_REPLAY_STOP_FILE=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/STOP-replay-mainnet-c FUSION_RESTART_HOST_STORAGE=/mnt/c GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=12h > "$results/replay.txt" 2>&1
code=$?
printf '%s\n' "$code" > "$results/exit-code.txt"
date -u +%FT%TZ > "$results/finished.txt"
du -sb "$target" > "$results/size.txt"
df -B1 --output=source,size,used,avail / /mnt/c /mnt/d > "$results/capacity-after.txt"
tail -n 10 "$results/replay.txt"
exit "$code"
