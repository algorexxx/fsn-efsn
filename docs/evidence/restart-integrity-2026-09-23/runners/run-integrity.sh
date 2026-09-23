set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-integrity
results=/home/rehearsal/results/restart-integrity-2026-09-23
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
mkdir -p "$mountpoint" "$results"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" | tee "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/isolation.txt"
sha256sum /home/rehearsal/integrity-tests >> "$results/isolation.txt"
date --utc --iso-8601=seconds | tee "$results/started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 GOMAXPROCS=2 /home/rehearsal/integrity-tests '-test.run=^TestPreserved(State|History)Integrity$' -test.v -test.timeout=12h > "$results/full-integrity.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/exit-code.txt"
date --utc --iso-8601=seconds | tee "$results/finished.txt"
tail -n 15 "$results/full-integrity.txt"
exit "$result"
