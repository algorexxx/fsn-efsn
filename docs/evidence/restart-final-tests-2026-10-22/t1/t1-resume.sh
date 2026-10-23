set -euo pipefail
FALLBACK=/home/rehearsal/replay/candidate-ticket-encoding-working
BACKUP=/home/rehearsal/data/efsn/chaindata
IMGDIR=/mnt/w/FusionRestart/t1-final-replay-2026-10-22
T1=/home/rehearsal/t1
SRC=/mnt/t1-source
DST=/mnt/t1-target
LOOP=""
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
cleanup() {
  set +e
  echo "$(stamp) cleanup"
  mountpoint -q $SRC && umount $SRC
  sync
  mountpoint -q $DST && umount $DST
  [ -n "$LOOP" ] && losetup -d $LOOP
  losetup --list | grep t1-final || echo "$(stamp) image detached"
}
trap cleanup EXIT

echo "$(stamp) resume; replay binary $(sha256sum $T1/replay.test | cut -c1-16)"
mkdir -p /mnt/w
mountpoint -q /mnt/w || mount -t drvfs W: /mnt/w -o uid=1000,gid=1000
df -h /mnt/w / | tail -2
[ -f $IMGDIR/replay.ext4 ] || { echo "refusing: no image to resume"; exit 1; }
rm -f $T1/STOP
LOOP=$(losetup --find --show $IMGDIR/replay.ext4)
mkdir -p $DST $SRC
mount $LOOP $DST
mount --bind $BACKUP $SRC
mount -o remount,bind,ro $SRC
touch $SRC/.write-probe 2>/dev/null && { echo "refusing: source is writable"; rm -f $SRC/.write-probe; exit 1; } || echo "$(stamp) source is read-only"
echo "$(stamp) replay starting"
runuser -u rehearsal -- env T1_SOURCE=$SRC T1_TARGET=$DST/checkpoint T1_END=15130080 T1_STOP_FILE=$T1/STOP \
  $T1/replay.test -test.run '^TestT1FinalReplay$' -test.v -test.timeout 200h
echo "$(stamp) replay finished"
df -h $DST | tail -1
