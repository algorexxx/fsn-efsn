set -euo pipefail
IMGDIR=/mnt/fusion/t1
T1=/home/peter/t1
STARTUP=/mnt/t1-startup
LOWER=$STARTUP/checkpoint
OVERLAY=/var/tmp/t1-source-overlay
SRC=/mnt/t1-source
DST=/mnt/t1-target
SRCLOOP=""
DSTLOOP=""
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
cleanup() {
  set +e
  echo "$(stamp) cleanup"
  mountpoint -q $SRC && umount $SRC
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
mountpoint -q $SRC && { echo "refusing: $SRC already mounted"; exit 1; }
mountpoint -q $DST && { echo "refusing: $DST already mounted"; exit 1; }
trap cleanup EXIT
df -h $IMGDIR / | tail -2
rm -f $T1/STOP
mkdir -p $DST $STARTUP $SRC
SRCLOOP=$(losetup --find --show --read-only $IMGDIR/startup.ext4)
mount -o ro,noload $SRCLOOP $STARTUP
touch $LOWER/.write-probe 2>/dev/null && { echo "refusing: source is writable"; rm -f $LOWER/.write-probe; exit 1; } || echo "$(stamp) source is read-only"
rm -rf $OVERLAY
mkdir -p $OVERLAY/upper $OVERLAY/work
chown peter:peter $OVERLAY/upper
mount -t overlay t1-source -o lowerdir=$LOWER,upperdir=$OVERLAY/upper,workdir=$OVERLAY/work $SRC
DSTLOOP=$(losetup --find --show $IMGDIR/replay.ext4)
mount $DSTLOOP $DST
echo "$(stamp) replay starting"
runuser -u peter -- env T1_SOURCE=$SRC T1_TARGET=$DST/checkpoint T1_END=15130080 T1_STOP_FILE=$T1/STOP \
  $T1/replay.test -test.run '^TestT1FinalReplay$' -test.v -test.timeout 400h
echo "$(stamp) replay finished"
df -h $DST | tail -1
