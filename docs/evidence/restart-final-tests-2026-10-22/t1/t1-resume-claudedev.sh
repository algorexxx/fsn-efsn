set -euo pipefail
IMGDIR=/mnt/fusion/t1
T1=/home/peter/t1
STARTUP=/mnt/t1-startup
SRC=$STARTUP/runtime/efsn/chaindata
DST=/mnt/t1-target
SRCLOOP=""
DSTLOOP=""
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
cleanup() {
  set +e
  echo "$(stamp) cleanup"
  mountpoint -q $STARTUP && umount $STARTUP
  sync
  mountpoint -q $DST && umount $DST
  [ -n "$SRCLOOP" ] && losetup -d $SRCLOOP
  [ -n "$DSTLOOP" ] && losetup -d $DSTLOOP
  losetup --list | grep -E 'startup|replay' || echo "$(stamp) images detached"
}

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
echo "$(stamp) resume; replay binary $(sha256sum $T1/replay.test | cut -c1-16)"
mountpoint -q /mnt/fusion || { echo "refusing: /mnt/fusion not mounted"; exit 1; }
[ -f $IMGDIR/replay.ext4 ] || { echo "refusing: no image to resume"; exit 1; }
losetup --list | grep -E 'startup.ext4|replay.ext4' && { echo "refusing: an image is already attached"; exit 1; }
mountpoint -q $STARTUP && { echo "refusing: $STARTUP already mounted"; exit 1; }
mountpoint -q $DST && { echo "refusing: $DST already mounted"; exit 1; }
trap cleanup EXIT
df -h $IMGDIR / | tail -2
rm -f $T1/STOP
mkdir -p $DST $STARTUP
SRCLOOP=$(losetup --find --show --read-only $IMGDIR/startup.ext4)
mount -o ro,noload $SRCLOOP $STARTUP
touch $SRC/.write-probe 2>/dev/null && { echo "refusing: source is writable"; rm -f $SRC/.write-probe; exit 1; } || echo "$(stamp) source is read-only"
DSTLOOP=$(losetup --find --show $IMGDIR/replay.ext4)
mount $DSTLOOP $DST
echo "$(stamp) replay starting"
runuser -u peter -- env T1_SOURCE=$SRC T1_TARGET=$DST/checkpoint T1_END=15130080 T1_STOP_FILE=$T1/STOP \
  $T1/replay.test -test.run '^TestT1FinalReplay$' -test.v -test.timeout 200h
echo "$(stamp) replay finished"
df -h $DST | tail -1
