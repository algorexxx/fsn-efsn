set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-replay-million
results=/home/rehearsal/results/restart-replay-million-2026-09-23
target=/home/rehearsal/replay/baseline-mainnet
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
test ! -e "$target"
mkdir -p "$mountpoint" "$results"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/isolation.txt"
sha256sum /home/rehearsal/replay-resume-tests >> "$results/isolation.txt"
date --utc --iso-8601=seconds | tee "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_END=1000000 FUSION_RESTART_REPLAY_STOP_FILE=/home/rehearsal/replay/STOP-baseline-mainnet FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=12h > "$results/replay.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/exit-code.txt"
date --utc --iso-8601=seconds | tee "$results/finished.txt"
du -sb "$target" > "$results/size.txt"
df -B1 --output=source,size,used,avail / /mnt/d > "$results/capacity.txt"
tail -n 10 "$results/replay.txt"
exit "$result"
