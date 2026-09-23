set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-replay-source
results=/home/rehearsal/results/restart-replay-100000-2026-09-23
target=/home/rehearsal/replay/baseline-100000
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test ! -e "$target"
mkdir -p "$mountpoint" "$results" /home/rehearsal/replay
chown rehearsal:rehearsal /home/rehearsal/replay
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/replay-isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/replay-isolation.txt"
sha256sum /home/rehearsal/replay-tests >> "$results/replay-isolation.txt"
date --utc --iso-8601=seconds | tee "$results/replay-started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_END=100000 FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=1h > "$results/replay-pilot.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/replay-exit-code.txt"
date --utc --iso-8601=seconds | tee "$results/replay-finished.txt"
du -sb "$target" > "$results/replay-size.txt"
df -B1 --output=source,size,used,avail / /mnt/d > "$results/replay-capacity.txt"
tail -n 15 "$results/replay-pilot.txt"
exit "$result"
