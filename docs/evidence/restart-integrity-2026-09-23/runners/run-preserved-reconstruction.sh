set -euo pipefail
variant=${1:?baseline or fixes}
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-reconstruction
results=/home/rehearsal/results/restart-integrity-2026-09-23
binary=/home/rehearsal/reconstruction-${variant}-tests
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
mkdir -p "$mountpoint"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/reconstruction-${variant}-isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/reconstruction-${variant}-isolation.txt"
sha256sum "$binary" >> "$results/reconstruction-${variant}-isolation.txt"
date --utc --iso-8601=seconds > "$results/reconstruction-${variant}-started.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
set +e
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 GOMAXPROCS=2 "$binary" '-test.run=^TestPreservedTicketReconstruction$' -test.v -test.timeout=20m > "$results/reconstruction-${variant}.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/reconstruction-${variant}-exit-code.txt"
date --utc --iso-8601=seconds > "$results/reconstruction-${variant}-finished.txt"
tail -n 8 "$results/reconstruction-${variant}.txt"
exit "$result"
